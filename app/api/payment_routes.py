from uuid import uuid4

from flask import Blueprint, jsonify, request, current_app

from app.models.plan import Plan
from app.models.payment import Payment
from app.models.user import User
from app.extensions import db
from app.services.paystack_service import PaystackService

payment_bp = Blueprint("payment", __name__)


@payment_bp.route("/initialize", methods=["POST"])
def initialize():

    data = request.get_json(silent=True) or {}

    if "plan_id" not in data:
        return jsonify({"success": False, "message": "plan_id is required."}), 400

    plan = Plan.query.get_or_404(data["plan_id"])

    email = data.get("email")

    if not email:
        return jsonify({
            "success": False,
            "message": "Email is required."
        }), 400

    # Captive portal customers don't have accounts: find or create a
    # lightweight guest user by email.
    user = User.query.filter_by(email=email).first()
    if not user:
        user = User(email=email)
        db.session.add(user)
        db.session.flush()

    reference = f"KSM-{uuid4().hex.upper()}"

    payment = Payment(
        user_id=user.id,
        plan_id=plan.id,
        amount_naira=plan.price_naira,
        reference=reference,
        status="pending",
    )

    db.session.add(payment)
    db.session.commit()

    callback_url = (
        f"{current_app.config['APP_BASE_URL']}"
        "/payment/success"
    )

    result = PaystackService.initialize_payment(
        email=email,
        amount=float(plan.price_naira),
        reference=reference,
        callback_url=callback_url,
    )

    checkout_url = result["data"]["authorization_url"]

    return jsonify({
        "success": True,
        "checkout_url": checkout_url,
        "reference": reference,
    })


@payment_bp.route("/status/<reference>")
def status(reference):
    """
    Polled by payment_success.html while waiting for the webhook to
    create the voucher (the customer is redirected back almost
    immediately after paying, often before the webhook has fired).
    """

    payment = Payment.query.filter_by(reference=reference).first_or_404()

    return jsonify({
        "status": payment.status,
        "voucher_code": payment.voucher.code if payment.voucher else None,
    })
