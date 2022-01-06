import datetime

import marshmallow
import sqlalchemy.exc
from flask import current_app, jsonify, request, Blueprint
from flask_jwt_extended import jwt_required

from views.auth import roles_required, get_current_user_custom
from config.extensions import db
from utils.mail_service import send_successful_reservation_notification, send_reservation_cancelled_notification
from models import Reservation, Arrangement, User
from schemas.schemas_rest import reservations_schema, reservation_schema, completed_reservation_schema

reservation_bp = Blueprint('reservations', __name__, url_prefix='/reservations')


@reservation_bp.get('/page/<int:page_id>')
@jwt_required()
@roles_required("ADMIN")
def get_all_reservations(page_id=1):
    if page_id <= 0:
        return {"msg", "Invalid page id."}, 400

    raw_reservations = db.session.execute(
        Reservation.query
            .limit(current_app.config['RESULTS_PER_PAGE'])
            .offset((page_id - 1) * current_app.config['RESULTS_PER_PAGE'])
    ).all()

    return jsonify([reservations_schema.dump(reservation) for reservation in raw_reservations])


@reservation_bp.get('/own')
@jwt_required()
@roles_required("TOURIST")
def get_own_reservations():
    current_user = get_current_user_custom()
    reservations = Reservation.query.filter_by(customer_id=current_user.id).all()

    return jsonify(reservations_schema.dump(reservations))


@reservation_bp.post('')
@jwt_required()
@roles_required("ADMIN", "TOURIST")
def create_reservation():
    try:
        user = get_current_user_custom()

        if user.account_type.name == "TOURIST":
            reservation = reservation_schema.load(request.get_json())
            reservation.customer_id = user.id

        else:
            req_customer_id = request.get_json()['customer']
            reservation = reservation_schema.load(request.get_json())
            reservation.customer_id = req_customer_id

        wanted_arrangement = Arrangement.query.filter_by(id=reservation.arrangement_id).first_or_404(
            description="No such arrangement found.")

        if wanted_arrangement.start_date - datetime.date.today() <= datetime.timedelta(days=5):
            return {"msg": "Wanted arrangement has expired."}, 404
        elif wanted_arrangement.seats_available < reservation.seats_needed:
            return {"msg": "There is not that much seats left."}, 404

        Reservation.query.session.add(reservation)
        Reservation.query.session.commit()

        send_successful_reservation_notification(user, reservation)

        return {
                   "msg": "Successfully appointed a reservation",
                   "reservation": completed_reservation_schema.dump(reservation)
               }, 200

    except sqlalchemy.exc.IntegrityError:
        return {"msg": "Already made such a reservation."}, 403

    except marshmallow.ValidationError as err:
        return err.messages, 400

    except KeyError:
        return {"msg": "Customer id missing."}, 400


@reservation_bp.delete('/<int:arrangement_id>')
@jwt_required()
@roles_required("ADMIN", "TOURIST")
def delete_reservation(arrangement_id):
    user = get_current_user_custom()
    if user.account_type.name == "TOURIST":
        reservation = Reservation.query.filter_by(arrangement_id=arrangement_id, customer_id=user.id) \
            .first_or_404(description="No such reservation found.")
    else:
        reservation = Reservation.query.filter_by(arrangement_id=arrangement_id) \
            .first_or_404(description="No such reservation found.")

    Reservation.query.session.delete(reservation)
    Reservation.query.session.commit()

    if user.account_type.name == "TOURIST":
        send_reservation_cancelled_notification(user, reservation)
    else:
        tourist = User.query.filter_by(id=reservation.customer_id) \
            .first_or_404(description="No such tourist found.")
        send_reservation_cancelled_notification(tourist, reservation)

    return {"msg": "Successfully canceled the reservation."}


@reservation_bp.put('/<int:arrangement_id>')
@jwt_required()
@roles_required("ADMIN", "TOURIST")
def update_reservation(arrangement_id):
    user = get_current_user_custom()

    try:
        if user.account_type.name == "TOURIST":
            reservation = Reservation.query.filter_by(arrangement_id=arrangement_id, customer_id=user.id) \
                .first_or_404(description="No such reservation found.")
        else:
            try:
                customer_id = request.get_json()['customer']
                reservation = Reservation.query.filter_by(arrangement_id=arrangement_id, customer_id=customer_id) \
                    .first_or_404(description="No such reservation found.")

            except KeyError:
                return {"msg": "Customer id missing."}, 400

        req_seats_needed = request.get_json()['seats_needed']

        arrangement = Arrangement.query.filter_by(id=reservation.arrangement_id) \
            .first_or_404(description="No such arrangement exists.")

        if arrangement.seats_available >= req_seats_needed:
            reservation.seats_needed = req_seats_needed
            Reservation.query.session.commit()

            send_successful_reservation_notification(user, reservation, True)

            return {"msg": "Reservation successfully updated.",
                    "reservation": completed_reservation_schema.dump(reservation)}

        return {"msg": "There is not enough seats needed. Reservation unchanged.",
                "reservation": completed_reservation_schema(reservation)}

    except KeyError:
        return {"msg": "Seats needed field is  missing."}, 400

    except TypeError:
        return {"msg": "Malformed request."}, 400
