import datetime

import marshmallow
from flask import request, current_app, jsonify, Blueprint
from flask_jwt_extended import jwt_required, verify_jwt_in_request
from sqlalchemy import select, text

from utils.mail_service import send_arrangement_cancelled_notification
from models.models import Arrangement, User, Reservation
from models.models import db
from schemas.schemas_rest import basic_arrangements_schema, arrangement_schema, arrangements_schema
from views.auth import roles_required, get_current_user_custom

arrangements_bp = Blueprint('arrangements', __name__, url_prefix='/arrangements')


@arrangements_bp.get('/page/<int:page>')
def get_all_arrangements(page=1):
    if page <= 0:
        return {"msg": "Invalid page number."}, 400

    # if user is logged in, the user gets fully detailed arrangements
    # otherwise basic info
    if verify_jwt_in_request(optional=True) is None:
        schema = basic_arrangements_schema
        select_statement = select(Arrangement.id, Arrangement.start_date, Arrangement.destination, Arrangement.price)
    else:
        schema = arrangements_schema
        select_statement = select(Arrangement.id, Arrangement.start_date, Arrangement.end_date, Arrangement.destination,
                                  Arrangement.price, Arrangement.number_of_seats, Arrangement.description)

    results_per_page = current_app.config.get('RESULTS_PER_PAGE')
    sorts = {
        "price-a": Arrangement.price.asc(),
        "price-d": Arrangement.price.desc(),
        "start-date-a": Arrangement.start_date.asc(),
        "start-date-d": Arrangement.start_date.desc(),
        "end-date-a": Arrangement.end_date.asc(),
        "end-date-d": Arrangement.end_date.desc(),
        "destination-a": Arrangement.destination.asc(),
        "destination-d": Arrangement.destination.desc(),
        "number-of-seats-a": Arrangement.number_of_seats.asc(),
        "number-of-seats-d": Arrangement.number_of_seats.desc(),
    }

    # if we're trying to get arrangements between specific dates
    # parse them from request and return the appropriate results
    req_start_date = request.args.get('start-date', None)
    req_end_date = request.args.get('end-date', None)
    if req_start_date and req_end_date:
        try:
            start_date = datetime.date.fromisoformat(req_start_date)
            end_date = datetime.date.fromisoformat(req_end_date)

            if end_date < start_date:
                return {"msg": "Malformed dates."}, 400

            select_statement = select_statement.filter(Arrangement.start_date >= start_date,
                                                       Arrangement.end_date <= end_date)

        except ValueError:
            return {"msg": "Invalid date format."}, 400

    req_destination = request.args.get('dest', None)
    if req_destination is not None:
        select_statement = select_statement.filter(Arrangement.destination.like(f"%{req_destination}%"))

    # if there is no sorting parameter in the request
    # or the parameter provided doesn't exist
    # we return the arrangements paginated by start_date
    # otherwise we use the provided param
    req_sort_param = request.args.get('sort', None)
    if req_sort_param is None or sorts.get(req_sort_param, None) is None:
        raw_arrangements = db.session.execute(
            select_statement
                .order_by(Arrangement.start_date.asc())
                .limit(results_per_page)
                .offset((page - 1) * results_per_page)
        ).all()
    else:
        sorting_param = sorts[req_sort_param]
        raw_arrangements = db.session.execute(
            select_statement
                .order_by(sorting_param)
                .limit(results_per_page)
                .offset((page - 1) * results_per_page)
        ).all()

    return jsonify(schema.dump(raw_arrangements))


@arrangements_bp.get('/<int:arrangement_id>')
@jwt_required()
def get_arrangement(arrangement_id):
    arrangement = Arrangement.query.filter_by(id=arrangement_id).first_or_404(description='No such arrangement found.')
    return arrangement_schema.dump(arrangement)


@arrangements_bp.get('/own')
@jwt_required()
@roles_required("ADMIN", "GUIDE")
def get_own_arrangements():
    user = get_current_user_custom()

    if user.account_type.name == "ADMIN":
        arrangements = Arrangement.query.filter_by(creator_id=user.id).all()
    else:
        arrangements = Arrangement.query.filter_by(guide_id=user.id).all()

    return jsonify(arrangements_schema.dump(arrangements))


@arrangements_bp.post('/')
@jwt_required()
@roles_required("ADMIN")
def create_arrangement():
    try:
        arrangement = arrangement_schema.load(request.get_json())
        user = get_current_user_custom()
        arrangement.creator_id = user.id
        Arrangement.query.session.add(arrangement)
        Arrangement.query.session.commit()

        return {
            "msg": "Arrangement successfully created.",
            "arrangement": arrangement_schema.dump(arrangement)
        }

    except marshmallow.ValidationError as error:
        return error.messages, 400


@arrangements_bp.put('/<int:arrangement_id>')
@jwt_required()
@roles_required("ADMIN", "GUIDE")
def update_arrangement(arrangement_id):
    user = get_current_user_custom()
    arrangement = Arrangement.query.filter_by(id=arrangement_id).first_or_404(description='No such arrangement found.')
    arrangement_was_cancelled = arrangement.cancelled

    if arrangement.start_date - datetime.date.today() <= datetime.timedelta(days=5):
        return {"msg": "Too late, arrangement editing time has passed."}, 403

    if user.account_type.name == "ADMIN" and arrangement.creator_id == user.id:
        try:
            request_arrangement = arrangement_schema.load(request.get_json())

            # if we're assigning a guide
            if request_arrangement.guide_id is not None:
                guide = User.query.filter_by(id=request_arrangement.guide_id).first_or_404(
                    description="There's no such guide.")
                if guide.account_type != "GUIDE":
                    return {"msg": "There's no such guide."}, 404

                # if guide is free on that day we assign him
                if guide.is_free(request_arrangement.start_date) and guide.is_free(request_arrangement.end_date):
                    arrangement.update(request_arrangement)
                else:
                    return {"msg": "Guide is not free on that day."}, 400
            else:
                # if we're not assigning a guide we just update the arrangement
                arrangement.update(request_arrangement)

            # either way we check if we're actually canceling the arrangement
            if request_arrangement.cancelled is True and arrangement_was_cancelled is False:
                users = db.session.query(User) \
                    .join(Reservation, User.id == Reservation.customer_id) \
                    .where(Reservation.arrangement_id == arrangement.id) \
                    .all()

                for user in users:
                    send_arrangement_cancelled_notification(user, arrangement)

            Arrangement.query.session.commit()

            return {
                "msg": "Arrangement updated successfully.",
                "arrangement": arrangement_schema.dump(arrangement)
            }

        except marshmallow.ValidationError as error:
            return error.messages, 400

    elif user.account_type.name == "GUIDE":
        try:
            description = request.get_json()["description"]

            arrangement = Arrangement.query.filter_by(id=arrangement_id).first_or_404(
                description="No such arrangement found.")

            if arrangement.guide_id != user.id:
                return {"msg": "Forbidden method."}, 403

            arrangement.description = description
            Arrangement.query.session.commit()
            return {"msg": "Successfully updated an description."}

        except KeyError:
            return {"msg": "Malformed request."}, 400


@arrangements_bp.delete('/<int:arrangement_id>')
@jwt_required()
@roles_required("ADMIN")
def delete_arrangement(arrangement_id):
    user = get_current_user_custom()
    arrangement = Arrangement.query.filter_by(id=arrangement_id, creator_id=user.id) \
        .first_or_404(description="There's no such arrangement.")

    users = db.session.query(User) \
        .join(Reservation, User.id == Reservation.customer_id) \
        .where(Reservation.arrangement_id == arrangement.id) \
        .all()

    for user in users:
        send_arrangement_cancelled_notification(user, arrangement)

    Arrangement.query.session.delete(arrangement)
    Arrangement.query.session.commit()

    return {"msg": "Successfully deleted an arrangement."}


@arrangements_bp.get('/available')
@jwt_required()
@roles_required("TOURIST")
def get_available_arrangements():
    current_user = get_current_user_custom()

    with db.engine.connect() as connection:
        query_text = text(
            'SELECT * FROM arrangement '
            'WHERE arrangement.start_date > CURRENT_DATE + 5 AND ('
            'SELECT COUNT(*) FROM reservation '
            'WHERE reservation.arrangement_id = arrangement.id AND reservation.customer_id = :curr_user_id'
            ') = 0;')

        available_arrangements = connection.execute(query_text, curr_user_id=current_user.id)

        return jsonify([arrangement_schema.dump(arrangement) for arrangement in available_arrangements])
