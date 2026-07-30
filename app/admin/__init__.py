from flask import Blueprint, session, redirect, request

admin_bp = Blueprint("admin", __name__, template_folder="../templates/admin")


@admin_bp.before_request
def require_login():
    """
    Runs before every route on admin_bp. This is the fix for the
    7 previously-unauthenticated admin routes (dashboard, vouchers,
    disable, delete, sync, settings, reports/summary).
    """

    if "admin_id" not in session:
        return redirect(f"/auth/login?next={request.path}")


# Import routes after admin_bp is defined so their @admin_bp.route
# decorators register against a blueprint that already has the guard.
from app.admin import routes           # noqa: E402,F401
from app.admin import voucher_routes   # noqa: E402,F401
from app.admin import settings_routes  # noqa: E402,F401
from app.admin import report_routes    # noqa: E402,F401
from app.admin import plan_routes      # noqa: E402,F401
