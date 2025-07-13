from flask import render_template, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required
from forms import LoginForm, RegistrationForm
from models import User, PostImage, Notification
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import login_manager, db
from flask_babel import _
from . import auth


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@auth.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            if user.role == "admin":
                return redirect(url_for("admin.admin_panel"))
            else:
                return redirect(url_for("client.dashboard"))
        else:
            flash(_("Login Unsuccessful. Please check username and password"), "danger")
    images = PostImage.query.limit(9).all()
    return render_template("login.html", form=form, images=images)


@auth.route("/register", methods=["GET", "POST"])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(
            form.password.data, method="pbkdf2:sha256"
        )
        user = User(
            full_name=form.full_name.data,
            username=form.username.data,
            email=form.email.data,
            whatsapp_number=form.whatsapp_number.data,
            password=hashed_password,
            role="client",
        )
        db.session.add(user)
        db.session.commit()

        # --- NOTIFICATION: New Client Registration --- #
        admins = User.query.filter_by(role="admin").all()
        for admin_user in admins:
            notification = Notification(
                user_id=admin_user.id,
                type="new_client",
                entity_id=user.id,
                message=f"Klien baru mendaftar: {user.username} ({user.email}).",
            )
            db.session.add(notification)
        db.session.commit()
        # --- END NOTIFICATION --- #

        flash(_("Your account has been created! You are now able to log in"), "success")
        return redirect(url_for("auth.login"))
    images = PostImage.query.limit(9).all()
    return render_template("register.html", form=form, images=images)


@auth.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("main.index"))
