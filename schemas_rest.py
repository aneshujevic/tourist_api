from datetime import datetime, date

from flask import request
from flask_marshmallow import fields
from markupsafe import escape
from marshmallow import validate, validates, pre_load, post_load

from extensions import ma
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

    id = ma.auto_field(dump_only=True)
    username = ma.auto_field(validate=[validate.Length])
    email = ma.auto_field(
        validate=[validate.Email(error="Not a valid email address."),
                  validate.Length(min=5, max=64, error="Invalid length of email address.")]
    )
    password = ma.auto_field(load_only=True, validate=[
        validate.Length(min=8, max=256, error="Invalid password length."),
    ])
    account_type = ma.auto_field(dump_only=True)

    def get_user_from_jwt_claims(self, data):
        self.id = data["id"]
        self.username = data["username"]
        self.email = data["email"]
        account_type = AccountType.query.filter_by(id=data["account_type"][0])\
            .first_or_404(description='Invalid account type')
        self.account_type = account_type

        return self

    @pre_load
    def process_input(self, data, **kwargs):
        data["username"] = escape(data["username"].strip())
        data["first_name"] = escape(data["first_name"].strip())
        data["last_name"] = escape(data["last_name"].strip())
        return data

    @post_load
    def make_user(self, data, **kwargs):
        return User(**data)


user_schema = UserSchema()
users_schema = UserSchema(many=True)


class ArrangementSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Arrangement
        load_instance = True

    id = ma.auto_field(dump_only=True)
    creator = ma.auto_field(dump_only=True)
    start_date = ma.auto_field()
    guide = ma.auto_field()
    description = ma.auto_field(validate=[
        validate.Length(min=5, error='Description too short, try adding some more comments.')
    ])
    destination = ma.auto_field(validate=[
        validate.Length(min=5, error='Destination too short, try adding some more comments.')
    ])
    seats_available = fields.fields.Integer()

    @validates('start_date')
    def validate_start_date_order(self, value):
        try:
            end_date = date.fromisoformat(request.get_json()['end_date'])
            if value > end_date:
                raise validate.ValidationError('Start date must be before the end date.')
        except ValueError as error:
            raise validate.ValidationError(str(error))

    @validates('end_date')
    def validate_end_date_order(self, value):
        try:
            start_date = date.fromisoformat(request.get_json()['start_date'])
            if value < start_date:
                raise validate.ValidationError('End date must be after the start date.')
        except ValueError as error:
            raise validate.ValidationError(str(error))

    @validates('number_of_seats')
    def validate_number_of_seats(self, value):
        if value <= 0:
            raise validate.ValidationError('Number of seats must not be 0.')

    @validates('price')
    def validate_price(self, value):
        if value <= 0:
            raise validate.ValidationError('Price must not be 0.')


arrangement_schema = ArrangementSchema()
arrangements_schema = ArrangementSchema(many=True)


class BasicArrangementSchema(ma.SQLAlchemySchema):
    class Meta:
        model = Arrangement
        load_instance = True

    id = ma.auto_field(dump_only=True)
    start_date = ma.auto_field(dump_only=True)
    destination = ma.auto_field(dump_only=True)
    price = ma.auto_field(dump_only=True)


basic_arrangement_schema = BasicArrangementSchema()
basic_arrangements_schema = BasicArrangementSchema(many=True)


class ReservationSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Reservation
        load_instance = True

    @validates('seats_needed')
    def validate_seats_needed(self, value):
        if value <= 0:
            raise validate.ValidationError('Seats needed must not be 0.')


reservation_schema = ReservationSchema()
reservations_schema = ReservationSchema(many=True)


class AccountTypeChangeRequestSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = AccountTypeChangeRequest
        load_instance = True

    id = ma.auto_field(dump_only=True)
    user = ma.auto_field(dump_only=True)
    filing_date = ma.auto_field(dump_only=True)
    confirmation_date = ma.auto_field(dump_only=True)
    admin_confirmed = ma.auto_field(dump_only=True)

    @pre_load
    def process_input(self, data, **kwargs):
        data["comment"] = escape(data["comment"])
        return data


account_type_change_request_schema = AccountTypeChangeRequestSchema()
account_type_change_requests_schema = AccountTypeChangeRequestSchema(many=True)
