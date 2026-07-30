from datetime import datetime
from app.extensions import db


class Device(db.Model):
    __tablename__ = "devices"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))

    voucher_id = db.Column(db.Integer, db.ForeignKey("vouchers.id"))

    mac_address = db.Column(db.String(17), unique=True, nullable=False)

    device_name = db.Column(db.String(120))

    first_seen = db.Column(db.DateTime, default=datetime.utcnow)

    last_seen = db.Column(db.DateTime, default=datetime.utcnow)

    is_active = db.Column(db.Boolean, default=True)
