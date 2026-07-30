"""
Run once to set up the database and create a default admin user:

    python seed.py

Set ADMIN_PASSWORD as an environment variable first to choose your own
password (recommended before going live) - e.g:

    ADMIN_PASSWORD=some-strong-password python seed.py

If ADMIN_PASSWORD isn't set, falls back to a random generated password
printed once to the console (safer than a fixed default like
"changeme123" sitting in a public repo/history forever).
"""

import os
import secrets

from app import create_app
from app.extensions import db
from app.models.admin import Admin
from app.models.setting import Setting

app = create_app()

with app.app_context():
    db.create_all()

    if not Admin.query.filter_by(username="admin").first():
        password = os.environ.get("ADMIN_PASSWORD") or secrets.token_urlsafe(12)

        admin = Admin(username="admin")
        admin.set_password(password)
        db.session.add(admin)

        print(f"Created default admin -> username: admin / password: {password}")
        print("SAVE THIS PASSWORD NOW - it will not be shown again.")
    else:
        print("Admin user already exists, skipping.")

    if not Setting.query.first():
        db.session.add(Setting())
        print("Created default settings row.")

    db.session.commit()
    print("Database ready.")
