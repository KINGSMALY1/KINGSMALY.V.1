from datetime import datetime
from app.extensions import db


class Setting(db.Model):
    __tablename__ = "settings"

    id = db.Column(db.Integer, primary_key=True)

    business_name = db.Column(db.String(120), default="Kingsmaly Starlink Network")

    support_phone = db.Column(db.String(20))

    support_email = db.Column(db.String(120))

    whatsapp_number = db.Column(db.String(20))

    currency = db.Column(db.String(10), default="NGN")

    timezone = db.Column(db.String(50), default="Africa/Lagos")

    logo = db.Column(db.String(255))

    # FIX: paystack_public_key is safe to store/display (it's meant to be
    # public), but the SECRET key must never live in the database.
    # It stays in env config only (current_app.config["PAYSTACK_SECRET_KEY"]),
    # read by PaystackService directly. Do not re-add a secret key column here.
    paystack_public_key = db.Column(db.String(255))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
