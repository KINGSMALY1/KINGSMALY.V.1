from flask import render_template, redirect, url_for, flash
from app.admin import admin_bp
from app.extensions import db
from app.models.voucher import Voucher
from app.services.voucher_service import VoucherService
from app.services.gwn_service import GWNService


@admin_bp.route("/vouchers")
def vouchers():

    vouchers = Voucher.query.order_by(
        Voucher.created_at.desc()
    ).all()

    return render_template(
        "admin/vouchers.html",
        vouchers=vouchers
    )


# FIX: was GET, now POST - prevents accidental/crawled destructive actions
@admin_bp.route("/voucher/<int:id>/disable", methods=["POST"])
def disable_voucher(id):

    voucher = Voucher.query.get_or_404(id)

    try:
        VoucherService.disable(voucher)
        flash("Voucher disabled successfully.", "success")
    except RuntimeError as e:
        flash(str(e), "danger")

    return redirect(url_for("admin.vouchers"))


# FIX: was GET, now POST. Also now attempts GWN-side removal, not just
# the local DB row, so the two systems don't drift apart.
@admin_bp.route("/voucher/<int:id>/delete", methods=["POST"])
def delete_voucher(id):

    voucher = Voucher.query.get_or_404(id)

    try:
        gwn = GWNService()
        gwn.disable_voucher(voucher.payment.reference)  # GWN has no separate delete-only call
    except RuntimeError as e:
        # Still proceed with local deletion, but let the admin know GWN
        # wasn't touched (e.g. voucher is currently in use there).
        flash(f"Note: GWN side not removed - {e}", "warning")

    db.session.delete(voucher)
    db.session.commit()

    flash("Voucher deleted locally.", "success")

    return redirect(url_for("admin.vouchers"))


# FIX: was GET, now POST
@admin_bp.route("/sync", methods=["POST"])
def sync():

    from app.services.sync_service import SyncService

    total = SyncService.sync_vouchers()

    flash(
        f"{total} vouchers synchronized.",
        "success"
    )

    return redirect(url_for("admin.vouchers"))
