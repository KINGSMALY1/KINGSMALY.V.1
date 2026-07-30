import hmac
import hashlib

from flask import Blueprint, request, jsonify, current_app

from app.extensions import db
from app.models.payment import Payment
from app.services.paystack_service import PaystackService
from app.services.voucher_service import VoucherService

webhook_bp = Blueprint("webhook", __name__)


@webhook_bp.route("/paystack", methods=["POST"])
def paystack_webhook():

    signature = request.headers.get("x-paystack-signature")

    payload = request.get_data()

    expected = hmac.new(
        current_app.config["PAYSTACK_SECRET_KEY"].encode(),
        payload,
        hashlib.sha512,
    ).hexdigest()

    # FIX: constant-time comparison instead of != to avoid timing attacks
    if not signature or not hmac.compare_digest(signature, expected):
        return jsonify({"error": "Invalid signature"}), 401

    event = request.get_json()

    if event["event"] != "charge.success":
        return jsonify({"message": "Ignored"}), 200

    reference = event["data"]["reference"]

    verify = PaystackService.verify_payment(reference)

    if not verify["status"]:
        return jsonify({"error": "Verification failed"}), 400

    payment = Payment.query.filter_by(reference=reference).first()

    if payment is None:
        return jsonify({"error": "Payment not found"}), 404

    if payment.session_created:
        return jsonify({"message": "Already processed"}), 200

    payment.status = "success"

    payment.paystack_transaction_id = str(
        verify["data"]["id"]
    )

    payment.paystack_raw_response = verify

    # FIX: goes through VoucherService now, which both calls GWN AND
    # saves the Voucher row locally (previously only the GWN side happened)
    voucher = VoucherService.create(payment)

    payment.session_created = True

    db.session.commit()

    return jsonify({
        "success": True,
        "voucher": voucher.code
    }), 200
