from flask import render_template, request, redirect, url_for, flash

from app.admin import admin_bp
from app.extensions import db
from app.models.plan import Plan


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
