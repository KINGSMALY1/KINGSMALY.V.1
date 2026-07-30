from flask import render_template, request, redirect, session, flash

from app.auth import auth_bp
from app.models.admin import Admin


@auth_bp.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        admin = Admin.query.filter_by(
            username=username
        ).first()

        if admin and admin.is_active and admin.check_password(password):

            session.clear()
            session["admin_id"] = admin.id

            return redirect("/admin")

        flash("Invalid username or password", "danger")

    return render_template("auth/login.html")


@auth_bp.route("/logout")
def logout():

    session.pop("admin_id", None)

    return redirect("/auth/login")
