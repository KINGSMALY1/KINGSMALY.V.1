from datetime import datetime
from app.extensions import db


class Session(db.Model):
    __tablename__ = "sessions"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))

    voucher_id = db.Column(db.Integer, db.ForeignKey("vouchers.id"))

    login_time = db.Column(db.DateTime, default=datetime.utcnow)

    logout_time = db.Column(db.DateTime)

    ip_address = db.Column(db.String(50))

    mac_address = db.Column(db.String(17))

    status = db.Column(
        db.Enum("online", "offline", name="session_status"),
        default="online"
    )
