from flask import current_app
from flask_mail import Message

from extensions import mail


def send_successful_registration(username, email, first_name, last_name):
    msg = Message(subject="Successful registration",
                  sender=current_app.config.get("MAIL_USERNAME"),
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
                  sender=current_app.config.get("MAIL_USERNAME"),
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
                  sender=current_app.config.get("MAIL_USERNAME"),
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
    msg = Message(subject=f"Cancelling of the reservation to {reservation.destination}",
                  sender=current_app.config.get("MAIL_USERNAME"),
                  recipients=[user.email],
                  body=f"Greetings {user.username}."
                       f"\n\nWe are sorry to inform you that the arrangement with id {reservation.arrangement_id} has been canceled."
                       f"\nHence your reservation is also cancelled."
                       f"\n\nWe are sorry for the inconvenience!"
                       f"\n\nBest of luck!"
                       f"\nAdmin team"
                  )
    mail.send(msg)
