import os
import secrets

from flask import Flask

from app.extensions import db


def create_app(config_object="config.Config"):

    app = Flask(__name__)
    app.config.from_object(config_object)

    db.init_app(app)

    from app.api import api_bp
    from app.portal import portal_bp
    from app.admin import admin_bp
    from app.auth import auth_bp

    app.register_blueprint(api_bp, url_prefix="/api")
    app.register_blueprint(portal_bp, url_prefix="/")
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(auth_bp, url_prefix="/auth")

    with app.app_context():
        _run_startup_setup(app)

    return app


def _run_startup_setup(app):
    """
    Creates DB tables and a default admin automatically on startup.

    This exists because Render's free tier has no Shell access, so
    seed.py can't be run interactively. Runs on every boot but is
    idempotent - safe to run repeatedly, does nothing once tables and
    the admin already exist. Output goes to Render's Logs tab.
    """
    from app.models.admin import Admin
    from app.models.setting import Setting
    from app.models.plan import Plan

    db.create_all()

    if not Admin.query.filter_by(username="admin").first():
        password = os.environ.get("ADMIN_PASSWORD") or secrets.token_urlsafe(12)

        admin = Admin(username="admin")
        admin.set_password(password)
        db.session.add(admin)

        print("=" * 60)
        print(f"CREATED DEFAULT ADMIN -> username: admin / password: {password}")
        print("SAVE THIS PASSWORD NOW - it will not be shown again in logs.")
        print("=" * 60)
    else:
        print("Admin user already exists, skipping creation.")

    if not Setting.query.first():
        db.session.add(Setting())
        print("Created default settings row.")

    if not app.config.get("PAYSTACK_SECRET_KEY"):
        print("WARNING: PAYSTACK_SECRET_KEY is not set - payments will fail.")

    if "localhost" in app.config.get("APP_BASE_URL", ""):
        print(
            "WARNING: APP_BASE_URL is still the localhost default. "
            "Paystack will reject the callback_url built from it (400 Bad "
            "Request on /transaction/initialize). Set APP_BASE_URL to your "
            "real live URL (e.g. https://kingsmaly.onrender.com) in "
            "Render -> Environment."
        )

    if not app.config.get("GWN_SECRET_KEY"):
        print("WARNING: GWN_SECRET_KEY is not set - voucher creation will fail.")

    if not Plan.query.first():
        # Matches the printed flyer pricing. Edit anytime at /admin/plans.
        db.session.add(Plan(name="15 Hours", price_naira=300, duration_minutes=900, sort_order=1))
        db.session.add(Plan(name="Weekly", price_naira=2000, duration_minutes=10080, sort_order=2))
        db.session.add(Plan(name="Monthly", price_naira=8000, duration_minutes=43200, sort_order=3))
        print("Created 3 starter plans (flyer pricing) - edit anytime at /admin/plans.")

    db.session.commit()
