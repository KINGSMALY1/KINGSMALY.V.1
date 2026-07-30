from flask import render_template

from app.admin import admin_bp
from app.models.setting import Setting


@admin_bp.route("/settings")
def settings():

    settings = Setting.query.first()

    return render_template(
        "admin/settings.html",
        settings=settings
    )
