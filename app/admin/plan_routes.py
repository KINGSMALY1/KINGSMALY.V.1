import random
import string

from flask import render_template, request, redirect, url_for, flash

from app.admin import admin_bp
from app.extensions import db
from app.models.plan import Plan


def _optional_number(value, cast):
    """Turn an empty form box into None (no limit), otherwise a number."""
    value = (value or "").strip()
    if not value:
        return None
    try:
        return cast(value)
    except ValueError:
        return None


@admin_bp.route("/plans")
def plans():

    all_plans = Plan.query.order_by(Plan.sort_order, Plan.id).all()

    return render_template("admin/plans.html", plans=all_plans)


@admin_bp.route("/plans/new", methods=["GET", "POST"])
def new_plan():

    if request.method == "POST":
        plan = Plan(
            name=request.form["name"].strip(),
            description=request.form.get("description", "").strip() or None,
            price_naira=request.form["price_naira"],
            duration_minutes=request.form["duration_minutes"],
            data_limit_gb=_optional_number(request.form.get("data_limit_gb"), float),
            speed_limit_mbps=_optional_number(request.form.get("speed_limit_mbps"), int),
            sort_order=request.form.get("sort_order", 0) or 0,
            is_active=True,
        )
        db.session.add(plan)
        db.session.commit()

        flash(f"Plan '{plan.name}' created.", "success")
        return redirect(url_for("admin.plans"))

    return render_template("admin/plan_form.html", plan=None)


@admin_bp.route("/plans/<int:id>/edit", methods=["GET", "POST"])
def edit_plan(id):

    plan = Plan.query.get_or_404(id)

    if request.method == "POST":
        plan.name = request.form["name"].strip()
        plan.description = request.form.get("description", "").strip() or None
        plan.price_naira = request.form["price_naira"]
        plan.duration_minutes = request.form["duration_minutes"]
        plan.data_limit_gb = _optional_number(request.form.get("data_limit_gb"), float)
        plan.speed_limit_mbps = _optional_number(request.form.get("speed_limit_mbps"), int)
        plan.sort_order = request.form.get("sort_order", 0) or 0

        db.session.commit()

        flash(f"Plan '{plan.name}' updated.", "success")
        return redirect(url_for("admin.plans"))

    return render_template("admin/plan_form.html", plan=plan)


@admin_bp.route("/plans/<int:id>/toggle", methods=["POST"])
def toggle_plan(id):

    plan = Plan.query.get_or_404(id)
    plan.is_active = not plan.is_active
    db.session.commit()

    flash(
        f"Plan '{plan.name}' is now {'active' if plan.is_active else 'hidden'}.",
        "success",
    )
    return redirect(url_for("admin.plans"))


@admin_bp.route("/gwn-probe")
def gwn_probe():
    """
    TEMPORARY. Tries different speed/data formats against GWN.Cloud and
    reports which ones it accepts. Every test voucher group that GWN
    accepts is deleted again straight away. Remove this route when done.
    """
    from flask import jsonify
    from app.services.gwn_service import GWNService

    gwn = GWNService()

    variants = [
        ("data 5120 unit1", {"usageQuota": 5120, "usageUnit": 1}),
        ("data 5000 unit1", {"usageQuota": 5000, "usageUnit": 1}),
        ("data 5 unit2", {"usageQuota": 5, "usageUnit": 2}),
        ("data 5120 no unit", {"usageQuota": 5120}),
        ("data 5 unit0", {"usageQuota": 5, "usageUnit": 0}),
        ("speed 5000 unit1", {"upRate": 5000, "upRateUnit": 1,
                              "downRate": 5000, "downRateUnit": 1}),
        ("speed 5 unit2", {"upRate": 5, "upRateUnit": 2,
                           "downRate": 5, "downRateUnit": 2}),
        ("speed 5120 unit1", {"upRate": 5120, "upRateUnit": 1,
                              "downRate": 5120, "downRateUnit": 1}),
        ("speed 5 unit0", {"upRate": 5, "upRateUnit": 0,
                           "downRate": 5, "downRateUnit": 0}),
    ]

    results = []

    for i, (label, extra) in enumerate(variants, start=1):
        name = f"probe-{i}"
        code = "PRB" + "".join(random.choice(string.ascii_uppercase) for _ in range(5))

        body = {
            "networkId": gwn.network_id,
            "name": name,
            "vocherNum": 1,
            "deviceNum": 1,
            "expiration": 30,
            "effectDurationMap": GWNService._duration_breakdown(900),
            "description": "probe - safe to delete",
            "usageLimitType": 0,
            "voucherType": 1,
            "passwords": [code],
        }
        body.update(extra)

        entry = {"variant": label, "sent": extra}

        try:
            result = gwn._signed_post("/oapi/v1.0.0/voucher/save", body)
            entry["retCode"] = result.get("retCode")
            entry["msg"] = result.get("msg")

            if result.get("retCode") == 0:
                try:
                    group_id = gwn.find_voucher_group_id(name)
                    if group_id is not None:
                        gwn.delete_voucher_group(group_id)
                        entry["cleanup"] = "test voucher group deleted"
                    else:
                        entry["cleanup"] = "could not find it to delete - remove 'probe-%d' by hand in GWN.Cloud" % i
                except Exception as e:
                    entry["cleanup"] = f"delete failed ({e}) - remove 'probe-{i}' by hand in GWN.Cloud"
        except Exception as e:
            entry["error"] = str(e)

        results.append(entry)

    return jsonify(results)
