from flask_marshmallow import fields
from marshmallow import validate

from app import ma
from models import Reservation, AccountType, Arrangement, AccountTypeChangeRequest, User


class AccountTypeSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = AccountType
        load_instance = True

    id = ma.auto_field(dump_only=True)
    name = ma.auto_field()


type_schema = AccountTypeSchema()
types_schema = AccountTypeSchema(many=True)


class UserSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = User
        load_instance = True

    id = ma.auto_field(dump_only=True)
    email = ma.auto_field(
        validate=[validate.Email(error="Not a valid email address."),
                  validate.Length(min=5, max=64, error="Invalid length of email address.")]
    )
    password = ma.auto_field(load_only=True, validate=[
        validate.Length(min=8, max=256, error="Invalid password length."),
    ])
    account_type = ma.Nested(AccountTypeSchema)


user_schema = UserSchema()
users_schema = UserSchema(many=True)


class ArrangementSchema(ma.SQLAlchemySchema):
    class Meta:
        model = Arrangement
        load_instance = True

    id = ma.auto_field()
    start_date = ma.auto_field()
    end_date = ma.auto_field()
    description = ma.auto_field()
    destination = ma.auto_field()
    number_of_seats = ma.auto_field()
    price = ma.auto_field()
    guide = ma.auto_field()
    creator = ma.auto_field()
    reservations = ma.auto_field()


arrangement_schema = ArrangementSchema()
arrangements_schema = ArrangementSchema(many=True)


class ReservationSchema(ma.SQLAlchemySchema):
    class Meta:
        model = Reservation
        load_instance = True

    customer = ma.auto_field()
    arrangement = ma.auto_field()
    seats_needed = ma.auto_field()


reservation_schema = ReservationSchema()
reservations_schema = ReservationSchema(many=True)


class AccountTypeChangeRequestSchema(ma.SQLAlchemySchema):
    class Meta:
        model = AccountTypeChangeRequest
        load_instance = True

    id = ma.auto_field()
    user = ma.auto_field()
    wanted_type = ma.auto_field()
    permission = ma.auto_field()
    filing_date = ma.auto_field()
    confirmation_date = ma.auto_field()
    admin_confirmed = ma.auto_field()
    comment = ma.auto_field()


account_type_change_request_schema = AccountTypeChangeRequestSchema()
account_type_change_requests_schema = AccountTypeChangeRequestSchema(many=True)
