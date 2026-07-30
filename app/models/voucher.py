from datetime import datetime
from app.extensions import db


class Voucher(db.Model):
    __tablename__ = "vouchers"

    id = db.Column(db.Integer, primary_key=True)

    code = db.Column(db.String(50), unique=True, nullable=False, index=True)

    payment_id = db.Column(
        db.Integer,
        db.ForeignKey("payments.id"),
        nullable=False
    )

    plan_id = db.Column(
        db.Integer,
        db.ForeignKey("plans.id"),
        nullable=False
    )

    # NOTE: kept for backward compat / quick lookups, but the Device table
    # is the real source of truth for which devices are using this voucher.
    # Consider dropping this column once Device is fully wired up.
    mac_address = db.Column(db.String(17), nullable=True)

    status = db.Column(
        db.Enum(
            "unused",
            "active",
            "expired",
            "disabled",
            name="voucher_status"
        ),
        default="unused",
        nullable=False
    )

    device_limit = db.Column(db.Integer, default=1)

    expires_at = db.Column(db.DateTime)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Voucher {self.code}>"
