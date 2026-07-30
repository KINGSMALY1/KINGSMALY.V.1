from datetime import datetime
from app.extensions import db


class Plan(db.Model):
    __tablename__ = "plans"

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(80), nullable=False)

    description = db.Column(db.String(255), nullable=True)

    price_naira = db.Column(db.Numeric(10, 2), nullable=False)

    duration_minutes = db.Column(db.Integer, nullable=False)

    is_active = db.Column(db.Boolean, default=True, nullable=False)

    sort_order = db.Column(db.Integer, default=0, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # one-to-many with Voucher
    vouchers = db.relationship(
        "Voucher",
        backref="plan",
        lazy="dynamic"
    )

    def __repr__(self):
        return f"<Plan {self.name}>"
