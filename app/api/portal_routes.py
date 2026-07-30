from datetime import datetime, timedelta

from flask import Blueprint, jsonify, request, session, current_app

from app.models.voucher import Voucher
from app.services.gwn_service import GWNService
from app.services.portal_params import extract_portal_params

portal_api_bp = Blueprint("portal_api", __name__)


@portal_api_bp.route("/connect", methods=["POST"])
def connect():
    """
    "Use it on this device" - authorizes the customer's device directly
    through GWN.Cloud's management API (POST /oapi/v1.0.0/portal/pass),
    server-to-server with the same HMAC signing used for voucher/save.

    The AP/client/SSID identifiers come from the query params the AP
    appended when it first redirected the browser to our splash page.
    Those param NAMES are still unconfirmed - see
    app/services/portal_params.py.
    """

    data = request.get_json(silent=True) or {}

    code = (data.get("code") or "").strip()

    if not code:
        return jsonify({"success": False, "message": "Voucher code is required."}), 400

    voucher = Voucher.query.filter_by(code=code).first()

    if voucher is None:
        return jsonify({"success": False, "message": "Voucher not found."}), 404

    if voucher.status == "disabled":
        return jsonify({"success": False, "message": "This voucher is no longer valid."}), 400

    # Prefer params on this request (the page may pass them through),
    # fall back to what we captured in the session at first contact.
    captured = dict(session.get("portal_params") or {})
    captured.update({k: v for k, v in request.args.items() if v})
    captured.update({k: v for k, v in data.items() if k != "code" and v})

    info = extract_portal_params(captured)

    missing = [
        name for name in ("client_mac", "ap_mac", "ssid_name")
        if not info.get(name)
    ]

    if missing:
        return jsonify({
            "success": False,
            "reason": "missing_portal_params",
            "missing": missing,
            "message": (
                "We couldn't detect this device from the WiFi login "
                "redirect. Enter the voucher on the WiFi login page instead."
            ),
        }), 409

    minutes = voucher.plan.duration_minutes if voucher.plan else 60

    start = datetime.utcnow()
    end = start + timedelta(minutes=minutes)

    try:
        GWNService().portal_pass(
            ap_mac=info["ap_mac"],
            client_mac=info["client_mac"],
            ssid_name=info["ssid_name"],
            start_use_time=int(start.timestamp() * 1000),
            end_use_time=int(end.timestamp() * 1000),
        )
    except Exception as exc:  # noqa: BLE001 - surface a usable message
        current_app.logger.exception("portal/pass failed for %s", code)
        return jsonify({"success": False, "message": str(exc)}), 502

    if voucher.status == "unused":
        voucher.status = "active"

    if not voucher.mac_address:
        voucher.mac_address = info["client_mac"]

    if voucher.expires_at is None:
        voucher.expires_at = end

    from app.extensions import db
    db.session.commit()

    return jsonify({
        "success": True,
        "redirect_url": info.get("redirect_url"),
        "minutes": minutes,
    })
