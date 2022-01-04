from sqlalchemy import CheckConstraint
from sqlalchemy.ext.hybrid import hybrid_property

from app import db

user_type_table = db.Table('user_type', db.metadata,
                           db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
                           db.Column('type_id', db.Integer, db.ForeignKey('type.id'), primary_key=True)
                           )


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, nullable=False)
    username = db.Column(db.String(32), unique=True, nullable=False)
    first_name = db.Column(db.String(32), nullable=False)
    last_name = db.Column(db.String(32), nullable=False)
    password = db.Column(db.Text, nullable=False)
    account_type = db.relationship('type', secondary=user_type_table, back_populates='users', lazy='select')


class Type(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(16), nullable=False)
    users = db.relationship(
        'User',
        secondary=user_type_table,
        back_populates='type',
        lazy='select'
    )


class Arrangement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    description = db.Column(db.Text, nullable=False)
    destination = db.Column(db.Text, nullable=False)
    number_of_seats = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Integer, nullable=False)
    guide = db.Column(db.ForeignKey('user.id'), nullable=True)
    creator = db.Column(db.ForeignKey('user.id'), nullable=False)
    reservations = db.relationship('Reservation', backref='arrangement')

    __table_args__ = (CheckConstraint(start_date < end_date, name='check_dates_correct'),
                      CheckConstraint(price > 0, name='check_price_positive'),
                      CheckConstraint(number_of_seats > 0, name='check_seats_number_positive'))

    @hybrid_property
    def seats_available(self):
        return self.number_of_seats - sum(reservation.seats_needed for reservation in self.reservations)


class Reservation(db.Model):
    customer = db.Column(db.ForeignKey('user.id'), nullable=False, primary_key=True)
    arrangement = db.Column(db.ForeignKey('arrangement.id'), nullable=False, primary_key=True)
    seats_needed = db.Column(db.Integer, nullable=False, default=1)

    __table_args__ = (CheckConstraint(seats_needed >= 0, name='check_seats_positive'),)

    @hybrid_property
    def price(self):
        return self.seats_needed * self.arrangement.price if self.seats_needed < 3 \
            else 3 * self.arrangement.price + 0.9 * (self.seats_needed - 3)


class AccountTypeChangeRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.ForeignKey('user.id'), nullable=False)
    wanted_type = db.Column(db.ForeignKey('type.id'), nullable=False)
    permission = db.Column(db.Boolean, nullable=True)
    filing_date = db.Column(db.DateTime, nullable=False)
    confirmation_date = db.Column(db.DateTime, nullable=True)
    admin_confirmed = db.Column(db.ForeignKey('user.id'), nullable=True)
    comment = db.Column(db.Text, nullable=False)
