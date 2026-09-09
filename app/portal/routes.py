from flask import render_template, request, session, current_app

from app.portal import portal_bp
from app.models.plan import Plan
from app.models.payment import Payment
from app.models.voucher import Voucher
from app.services.portal_params import PORTAL_PARAM_KEYS


# Query params a GWN captive portal appends when it bounces a client to
# the splash page. We stash them in the session at first contact so that
# after the Paystack round-trip we can still authorize the very same
# device through GWN.Cloud's portal/pass API.
#
# NOTE: the exact names are UNCONFIRMED - see app/services/portal_params.py
# for the list we assume and normalize.


def _capture_portal_params():
    captured = {
        key: value
        for key, value in request.args.items()
        if key.lower() in PORTAL_PARAM_KEYS and value
    }

    if captured:
        merged = dict(session.get("portal_params") or {})
        merged.update(captured)
        session["portal_params"] = merged

    return session.get("portal_params", {})



@portal_bp.route("/")
def home():

    _capture_portal_params()

    plans = (
        Plan.query
        .filter_by(is_active=True)
        .order_by(Plan.sort_order)
        .all()
    )

    return render_template(
        "portal/index.html",
        plans=plans
    )


@portal_bp.route("/payment/success")
def payment_success():

    # Paystack appends ?reference=... on redirect back from checkout
    # Paystack appends ?reference=..., Monnify appends ?paymentReference=...
    reference = request.args.get("reference") or request.args.get("paymentReference")

    voucher_code = None

    if reference:
        payment = Payment.query.filter_by(reference=reference).first()
        if payment and payment.voucher:
            voucher_code = payment.voucher.code

    # If voucher_code is still None here, the webhook likely hasn't
    # fired yet - the template polls /api/payment/status/<reference>
    # until it's ready.
    return render_template(
        "portal/payment_success.html",
        voucher_code=voucher_code,
        reference=reference,
        portal_auth_url=current_app.config.get("GWN_PORTAL_AUTH_URL", ""),
        portal_params=session.get("portal_params", {}),
        app_base_url=current_app.config.get("APP_BASE_URL", ""),
    )


@portal_bp.route("/voucher/<code>")
def voucher_view(code):
    """
    Landing page the QR code points at, so the person the voucher was
    bought for can open it on their own phone, see the code and connect.
    """

    voucher = Voucher.query.filter_by(code=code).first()

    _capture_portal_params()

    return render_template(
        "portal/voucher.html",
        code=code,
        voucher=voucher,
        portal_auth_url=current_app.config.get("GWN_PORTAL_AUTH_URL", ""),
        portal_params=session.get("portal_params", {}),
    )


@portal_bp.route("/payment/failed")
def payment_failed():

    return render_template(
        "portal/payment_failed.html"
    )
