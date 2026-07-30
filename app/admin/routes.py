from flask import render_template

from app.extensions import db
from app.admin import admin_bp
from app.models.payment import Payment
from app.models.voucher import Voucher
from app.models.plan import Plan
from app.models.user import User


@admin_bp.route("/")
def dashboard():

    total_users = User.query.count()

    total_plans = Plan.query.count()

    total_payments = Payment.query.count()

    total_vouchers = Voucher.query.count()

    # FIX: sum in the database instead of pulling every row into Python
    total_revenue = db.session.query(
        db.func.coalesce(db.func.sum(Payment.amount_naira), 0)
    ).filter(Payment.status == "success").scalar()

    total_revenue = float(total_revenue)

    return render_template(
        "admin/dashboard.html",
        total_users=total_users,
        total_plans=total_plans,
        total_payments=total_payments,
        total_vouchers=total_vouchers,
        revenue=total_revenue,
    )
