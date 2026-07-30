from datetime import date

from flask import jsonify

from app.admin import admin_bp
from app.models.payment import Payment


@admin_bp.route("/reports/summary")
def report_summary():

    today = date.today()

    payments = (
        Payment.query
        .filter(Payment.status == "success")
        .all()
    )

    revenue = sum(
        float(p.amount_naira)
        for p in payments
    )

    today_revenue = sum(
        float(p.amount_naira)
        for p in payments
        if p.created_at.date() == today
    )

    return jsonify({

        "today_revenue": today_revenue,

        "total_revenue": revenue,

        "payments": len(payments)

    })
