from time import time

import jwt
import marshmallow
from flask import current_app
from sqlalchemy import CheckConstraint, select, and_
from sqlalchemy.ext.hybrid import hybrid_property, hybrid_method

from config.extensions import db

user_type_table = db.Table('user_type', db.metadata,
                           db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
                           db.Column('account_type_id', db.Integer, db.ForeignKey('account_type.id'), primary_key=True)
                           )


class AccountType(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    users = db.relationship(
        'User',
        secondary=user_type_table,
        back_populates='account_type',
        lazy='select'
    )

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, nullable=False)
    username = db.Column(db.String(32), unique=True, nullable=False)
    first_name = db.Column(db.String(32), nullable=False)
    last_name = db.Column(db.String(32), nullable=False)
    password = db.Column(db.String(512), nullable=False)
    account_type = db.relationship('AccountType', secondary=user_type_table, back_populates='users', lazy='select')

    def update(self, other):
        self.email = other.email
        self.username = other.username
        self.first_name = other.first_name
        self.last_name = other.last_name
        self.password = other.password

    def get_reset_token(self, expires=500):
        return jwt.encode(
            {'reset_password': self.username, 'exp': time() + expires},
            key=current_app.config.get("JWT_SECRET_KEY")
        )

    @hybrid_property
    def reservations(self):
        for acc_type in self.account_type:
            if "TOURIST" in acc_type.name:
                reservations = Reservation.query.filter_by(customer_id=self.id)
                return reservations
            raise TypeError("Not a tourist account")

    @hybrid_property
    def guiding_tours(self):
        for acc_type in self.account_type:
            if "GUIDE" in acc_type.name:
                arrangements = Arrangement.query.filter_by(guide_id=self.id).all()
                return arrangements
            raise TypeError("Not a guide account")

    @hybrid_method
    def is_free(self, date_needed):
        for acc_type in self.account_type:
            if "GUIDE" in acc_type.name:
                # only one is needed for us to know that the guide is busy
                arrangements = db.session.execute(
                    select(Arrangement.id)
                        .where(
                        and_(Arrangement.start_date <= date_needed, date_needed <= Arrangement.end_date)
                    )
                ).first()

                if arrangements is None:
                    return True
                return False
            raise TypeError("Not a guide account.")


class Arrangement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    description = db.Column(db.Text, nullable=False)
    destination = db.Column(db.Text, nullable=False)
    cancelled = db.Column(db.Boolean, default=False)
    number_of_seats = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    guide_id = db.Column(db.ForeignKey('user.id'), nullable=True)
    creator_id = db.Column(db.ForeignKey('user.id'), nullable=False)
    reservations = db.relationship('Reservation', backref='arrangements_id')

    __table_args__ = (CheckConstraint(start_date < end_date, name='check_dates_correct'),
                      CheckConstraint(price > 0, name='check_price_positive'),
                      CheckConstraint(number_of_seats > 0, name='check_seats_number_positive'))

    @hybrid_property
    def seats_available(self):
        return self.number_of_seats - sum(reservation.seats_needed for reservation in self.reservations)

    def update(self, other):
        if not self.cancelled:
            self.start_date = other.start_date
            self.end_date = other.end_date
            self.description = other.description
            self.destination = other.destination
            self.number_of_seats = other.number_of_seats
            self.price = other.price
            self.guide_id = other.guide_id
            self.cancelled = other.cancelled
        else:
            raise marshmallow.ValidationError(message='Arrangement is cancelled, therefore it cannot be changed.')


class Reservation(db.Model):
    seats_needed = db.Column(db.Integer, nullable=False)
    customer_id = db.Column(db.ForeignKey('user.id'), nullable=False, primary_key=True)
    arrangement_id = db.Column(db.ForeignKey('arrangement.id'), nullable=False, primary_key=True)

    __table_args__ = (CheckConstraint(seats_needed >= 0, name='check_seats_positive'),)

    @hybrid_property
    def reservation_price(self):
        arrangement = Arrangement.query.filter_by(id=self.arrangement_id).first()

        if self.seats_needed < 3:
            result = self.seats_needed * arrangement.price
        else:
            result = 3 * arrangement.price + 0.9 * (self.seats_needed - 3)

        return result

    @hybrid_property
    def customer_details(self):
        user = User.query.filter_by(id=self.customer_id).first()

        return user


class AccountTypeChangeRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.ForeignKey('user.id'), nullable=False)
    wanted_type_id = db.Column(db.ForeignKey('account_type.id'), nullable=False)
    filing_date = db.Column(db.DateTime, nullable=False)
    confirmation_date = db.Column(db.DateTime, nullable=True)
    admin_confirmed_id = db.Column(db.ForeignKey('user.id'), nullable=True)
    granted = db.Column(db.Boolean, nullable=True)
    comment = db.Column(db.Text, nullable=True)

    @hybrid_property
    def wanted_type(self):
        acc_type = AccountType.query.filter_by(id=self.wanted_type_id).first()
        return acc_type.name

    def update(self, other):
        self.confirmation_date = other.confirmation_date
        self.admin_confirmed_id = other.admin_confirmed_id
        self.comment = other.comment
