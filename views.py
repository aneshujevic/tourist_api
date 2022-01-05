import datetime

import flask
import marshmallow
from flask import Blueprint, request, current_app, jsonify
from flask_jwt_extended import jwt_required, verify_jwt_in_request
from sqlalchemy import select, and_

# from auth import get_current_user_custom
import app
from auth import get_current_user_custom
from models import Arrangement, User, AccountType
from models import db
from schemas_rest import basic_arrangements_schema, arrangement_schema, user_schema, arrangements_schema

arrangements_bp = Blueprint('arrangements', __name__, url_prefix='/arrangements')
users_bp = Blueprint('users', __name__, url_prefix='/users')


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

            raw_arrangements = db.session.execute(
                select_statement
                    .filter(Arrangement.start_date >= start_date, Arrangement.end_date <= end_date)
                    .limit(results_per_page)
                    .offset((page - 1) * results_per_page)
            ).all()

            return jsonify(schema.dump(raw_arrangements))

        except ValueError:
            return {"msg": "Invalid date format."}, 400

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
def get_arrangement(arrangement_id):
    arrangement = Arrangement.query.filter_by(id=arrangement_id).first_or_404(description='No such arrangement found.')
    return arrangement_schema.dump(arrangement)


@arrangements_bp.post('/')
@jwt_required()
def create_arrangement():
    try:
        arrangement = arrangement_schema.load(request.get_json())
        user = get_current_user_custom()
        arrangement.creator = user.id
        Arrangement.query.session.add(arrangement)
        Arrangement.query.session.commit()

        return {"msg": "Arrangement successfully created."}

    except marshmallow.ValidationError as error:
        return error.messages, 400


@arrangements_bp.put('/<int:arrangement_id>')
@jwt_required()
def update_arrangement(arrangement_id):
    user = get_current_user_custom()
    arrangement = Arrangement.query.filter_by(id=arrangement_id).first_or_404(description='No such arrangement found.')

    if arrangement.start_date - datetime.date.today() <= datetime.timedelta(days=5):
        return {"msg": "Too late, arrangement editing time has passed."}, 403

    if user.account_type.name == "ADMIN" and arrangement.creator == user.id:
        try:
            request_arrangement = arrangement_schema.load(request.get_json())

            # if we're assigning a guide
            if request_arrangement.guide is not None:
                guide = User.query.filter_by(id=request_arrangement.guide).first_or_404("There's no such guide.")
                if guide.account_type is not "GUIDE":
                    return {"msg": "There's no such guide."}, 404

                # if guide is free on that day we assign him
                if guide.check_free(request_arrangement.start_date) and guide.check_free(request_arrangement.end_date):
                    arrangement.update(request_arrangement)
                else:
                    return {"msg": "Guide is not free on that day."}, 400
            else:
                # if we're not assigning a guide we just update the arrangement
                arrangement.update(request_arrangement)

            # either way we check if we're actually canceling the arrangement
            if request_arrangement.cancelled is True and arrangement.cancelled is False:
                # TODO: notify all the users that the arrangement has been cancelled
                pass

            Arrangement.query.session.commit()

            return {"msg": "Arrangement updated successfully."}

        except marshmallow.ValidationError as error:
            return error.messages, 400

    elif user.account_type.name == "GUIDE":
        try:
            description = request.get_json()["description"]

            arrangement = Arrangement.query.filter_by(id=arrangement_id).first_or_404("No such arrangement found.")

            if arrangement.guide != user.id:
                return {"msg": "Forbidden method."}, 403

            arrangement.description = description
            Arrangement.query.session.commit()
            return {"msg": "Successfully updated an description."}

        except KeyError:
            return {"msg": "Malformed request."}, 400

