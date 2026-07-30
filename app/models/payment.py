from datetime import datetime
from app.extensions import db


class Payment(db.Model):
    __tablename__ = "payments"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    plan_id = db.Column(
        db.Integer,
        db.ForeignKey("plans.id"),
        nullable=False
    )

    amount_naira = db.Column(db.Numeric(10, 2), nullable=False)

    reference = db.Column(db.String(120), unique=True, nullable=False, index=True)

    status = db.Column(
        db.Enum(
            "pending",
            "success",
            "failed",
            name="payment_status"
        ),
        default="pending",
        nullable=False
    )

    paystack_transaction_id = db.Column(db.String(50), nullable=True)

    paystack_raw_response = db.Column(db.JSON, nullable=True)

    # Tracks whether the webhook has already generated a voucher for this
    # payment, so retried/duplicate webhook calls don't create duplicates.
    session_created = db.Column(db.Boolean, default=False, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # one-to-one with Voucher
    voucher = db.relationship(
        "Voucher",
        backref="payment",
        uselist=False
    )

    plan = db.relationship("Plan")

    def __repr__(self):
        return f"<Payment {self.reference} {self.status}>"
