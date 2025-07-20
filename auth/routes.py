from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from forms import LoginForm, RegistrationForm, RequestResetForm, ResetPasswordForm
from models import User, PostImage, Notification
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import login_manager, db, mail
from tasks import send_email_task # Import Celery task
from flask_mail import Message
from flask_babel import _
from . import auth


def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message('Permintaan Reset Kata Sandi', recipients=[user.email])
    msg.html = render_template('emails/reset_password.html', user=user, token=token)
    send_email_task.delay(
        subject=msg.subject,
        sender=msg.sender,
        recipients=msg.recipients,
        body=msg.html # Mengirim HTML sebagai body
    )


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@auth.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
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
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
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

        # Send confirmation email
        try:
            msg = Message("Pendaftaran Berhasil di Aruna Moment", recipients=[user.email])
            msg.html = render_template("emails/signup_confirmation.html", user=user)
            send_email_task.delay(
                subject=msg.subject,
                sender=msg.sender,
                recipients=msg.recipients,
                body=msg.html # Mengirim HTML sebagai body
            )
            flash(_("Akun Anda telah dibuat! Email konfirmasi telah dikirim."), "success")
        except Exception as e:
            flash(_("Akun Anda telah dibuat, tetapi gagal mengirim email konfirmasi. Silakan hubungi dukungan."), "warning")
            print(f"Error sending email: {e}")

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

        return redirect(url_for("auth.login"))
    images = PostImage.query.limit(9).all()
    return render_template("register.html", form=form, images=images)


@auth.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("main.index"))


@auth.route("/reset_password", methods=["GET", "POST"])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_reset_email(user)
            flash(_('Email dengan instruksi untuk mereset kata sandi Anda telah dikirim.'), 'info')
            return redirect(url_for('auth.login'))
    return render_template('reset_request.html', title='Reset Password', form=form)


@auth.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    user = User.verify_reset_token(token)
    if user is None:
        flash(_('Itu adalah token yang tidak valid atau kadaluarsa'), 'warning')
        return redirect(url_for('auth.reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data, method='pbkdf2:sha256')
        user.password = hashed_password
        db.session.commit()
        flash(_('Kata sandi Anda telah diperbarui! Anda sekarang dapat login.'), 'success')
        return redirect(url_for('auth.login'))
    return render_template('reset_token.html', title='Reset Password', form=form)
