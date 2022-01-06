import time

from flask import current_app
from flask_mail import Message

from config.extensions import mail


def send_successful_registration(username, email, first_name, last_name):
    msg = Message(subject="Successful registration",
                  recipients=[email],
                  body=f"Greetings {username}."
                       f"\n\nYou have successfully registered."
                       f"\n\nYour basic account info is {first_name} {last_name}."
                       f"\nYou have been assigned a tourist account."
                       f"\n\nFarewell!"
                       f"\nAdmin team"
                  )
    mail.send(msg)


def send_account_change_request_notification(user, acc_type_change_request):
    msg = Message(subject="Account type change request process",
                  recipients=[user.email],
                  body=f"Greetings {user.username}."
                       f"\n\nYour account type change request has been processed."
                       f"\n\nYour request has been {'granted' if acc_type_change_request.granted else 'denied'}."
                       f"\nAdmin comment is following:\n'{acc_type_change_request.comment}'"
                       f"\n\nDate: {acc_type_change_request.confirmation_date}"
                       f"\n\nFarewell!"
                       f"\nAdmin team"
                  )
    mail.send(msg)


def send_successful_reservation_notification(user, reservation, change=False):
    msg = Message(subject=f"Successful reservation {'change' if change else ''} to {reservation.destination}",
                  recipients=[user.email],
                  body=f"Greetings {user.username}."
                       f"\n\nYour have successfully {'changed' if change else 'made'} an reservation!"
                       f"\n\nYour reservation information is following:"
                       f"\nArrangement id: {reservation.arrangement_id}"
                       f"\nReservation price: {reservation.reservation_price}"
                       f"\nNumber of seats: {reservation.seats_needed}"
                       f"\nDestination: {reservation.destination}"
                       f"\n\nHave a sound trip!"
                       f"\nAdmin team"
                  )
    mail.send(msg)


def send_reservation_cancelled_notification(user, reservation):
    msg = Message(subject=f"Reservation to {reservation.destination} CANCELED",
                  recipients=[user.email],
                  body=f"Greetings {user.username}."
                       f"\nWe are sorry to inform you that your reservation for arrangement {reservation.arrangement_id} has been cancelled. "
                       f"\n\nSorry for the inconvenience!"
                       f"\n\nBest of luck!"
                       f"\nAdmin team"
                  )
    mail.send(msg)


def send_arrangement_cancelled_notification(user, arrangement):
    msg = Message(subject=f"Cancelling of the arrangement {arrangement.destination}",
                  recipients=[user.email],
                  body=f"Greetings {user.username}."
                       f"\n\nWe are sorry to inform you that the arrangement with id {arrangement.id} has been canceled."
                       f"\nHence your reservation is also cancelled."
                       f"\n\nWe are sorry for the inconvenience!"
                       f"\n\nBest of luck!"
                       f"\nAdmin team"
                  )
    mail.send(msg)


def send_password_reset_email(email, token):
    msg = Message(subject=f"Password reset",
                  recipients=[email],
                  body=f"Greetings,"
                       f"\n\nYou have requested a password reset."
                       f"\nYou should send a JSON request with password and password1 strings via POST method on "
                       f"{current_app.config.get('CURRENT_DOMAIN')}/auth/reset-password/{token}"
                       f"\n\nWe are sorry for the inconvenience!"
                       f"\n\nBest of luck!"
                       f"\nAdmin team"
                  )
    mail.send(msg)


def send_password_changed_email(user):
    msg = Message(subject="Password changed notification",
                  recipients=[user.email],
                  body=f"Greetings {user.username},"
                       f"\n\nYour password has been successfully changed."
                       f"\nTimestamp:{time.time()}"
                       f"\n\nBest of luck!"
                       f"\nAdmin team"
                  )
    mail.send(msg)
