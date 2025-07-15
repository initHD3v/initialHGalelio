from flask import (
    render_template,
    redirect,
    url_for,
    flash,
    request,
    current_app,
    send_file,
)
from flask_login import login_required, current_user
from flask_mail import Message
from extensions import mail
from models import (
    Order,
    Testimonial,
    db,
    BankAccount,
    Notification,
    User,
    CalendarEvent,
)
from admin.routes import send_cancellation_email_to_client, send_cancellation_notification_to_admin, send_reschedule_email_to_client, send_reschedule_notification_to_admin
from forms import (
    TestimonialSubmissionForm,
    TestimonialEditForm,
    UserEditForm,
    DPPaymentForm,
)
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename  # Added import
import os
from datetime import datetime, timedelta  # Added timedelta
import pytz  # Added pytz
from client import client

JAKARTA_TZ = pytz.timezone("Asia/Jakarta")

def send_new_order_notification_to_admin(order):
    try:
        admins = User.query.filter_by(role="admin").all()
        for admin_user in admins:
            msg = Message(
                f"Pesanan Baru Ditempatkan: {order.wedding_package.name if order.wedding_package else (order.prewedding_package.name if order.prewedding_package else order.service_type)}",
                recipients=[admin_user.email]
            )
            msg.html = render_template(
                'emails/new_order_notification.html',
                order=order,
                current_year=datetime.now().year
            )
            mail.send(msg)
    except Exception as e:
        current_app.logger.error(f"Failed to send new order notification email for order {order.id}: {e}")


@client.app_template_global("get_testimonial_for_order")
def get_testimonial_for_order(order_id):
    return Testimonial.query.filter_by(
        order_id=order_id, user_id=current_user.id
    ).first()


@client.route("/dashboard")
@login_required
def dashboard():
    orders = Order.query.filter_by(client_id=current_user.id).all()
    now = datetime.now(pytz.utc)
    upcoming_orders = [
        order
        for order in orders
        if order.status not in ["completed", "rejected", "expired", "cancelled"]
    ]
    history_orders = [
        order
        for order in orders
        if order.status in ["completed", "rejected", "expired", "cancelled"]
    ]

    # Fetch notifications for the current user
    notifications = (
        Notification.query.filter_by(user_id=current_user.id, is_read=False)
        .order_by(Notification.timestamp.desc())
        .all()
    )

    return render_template(
        "client/dashboard.html",
        orders=orders,
        now=now,
        upcoming_orders=upcoming_orders,
        history_orders=history_orders,
        notifications=notifications,
    )


@client.route("/submit_testimonial/<int:order_id>", methods=["GET", "POST"])
@login_required
def submit_testimonial(order_id):
    order = Order.query.get_or_404(order_id)

    # Ensure the order belongs to the current user
    if order.client_id != current_user.id:
        flash(
            "You do not have permission to submit a testimonial for this order.",
            "danger",
        )
        return redirect(url_for("client.dashboard"))

    # Ensure the order is completed and allows testimonial submission
    if order.status != "completed" or not order.can_submit_testimonial:
        flash(
            "This order is not yet completed or does not allow testimonial submission.",
            "danger",
        )
        return redirect(url_for("client.dashboard"))

    # Ensure client hasn't already submitted a testimonial for this order
    existing_testimonial = Testimonial.query.filter_by(
        order_id=order_id, user_id=current_user.id
    ).first()
    if existing_testimonial:
        flash("You have already submitted a testimonial for this order.", "warning")
        return redirect(url_for("client.dashboard"))

    form = TestimonialSubmissionForm()
    if form.validate_on_submit():
        testimonial = Testimonial(
            client_name=current_user.full_name,  # Use client's full name
            testimonial_text=form.testimonial_text.data,
            rating=form.rating.data,
            user_id=current_user.id,
            order_id=order.id,
            is_approved=False,  # Admin needs to approve
        )
        db.session.add(testimonial)
        db.session.commit()

        # --- NOTIFICATION: New Testimonial --- #
        admins = User.query.filter_by(role="admin").all()
        for admin_user in admins:
            notification = Notification(
                user_id=admin_user.id,
                type="new_testimonial",
                entity_id=testimonial.id,
                message=(
                    f"Testimoni baru dari {current_user.username} menunggu "
                    "persetujuan."
                ),
            )
            db.session.add(notification)
        db.session.commit()
        # --- END NOTIFICATION --- #

        flash("Your testimonial has been submitted for review!", "success")
        return redirect(url_for("client.dashboard"))

    return render_template("client/submit_testimonial.html", form=form, order=order)


@client.route("/edit_testimonial/<int:testimonial_id>", methods=["GET", "POST"])
@login_required
def edit_testimonial_client(testimonial_id):
    testimonial = Testimonial.query.get_or_404(testimonial_id)

    # Ensure the testimonial belongs to the current user
    if testimonial.user_id != current_user.id:
        flash("You do not have permission to edit this testimonial.", "danger")
        return redirect(url_for("client.dashboard"))

    # Prevent editing if already approved by admin
    if testimonial.is_approved:
        flash(
            "This testimonial has already been approved and cannot be edited.",
            "warning",
        )
        return redirect(url_for("client.dashboard"))

    form = TestimonialEditForm()
    if form.validate_on_submit():
        testimonial.testimonial_text = form.testimonial_text.data
        testimonial.rating = form.rating.data
        db.session.commit()
        flash("Your testimonial has been updated!", "success")
        return redirect(url_for("client.dashboard"))
    elif request.method == "GET":
        form.testimonial_text.data = testimonial.testimonial_text
        form.rating.data = testimonial.rating

    return render_template(
        "client/edit_testimonial.html", form=form, testimonial=testimonial
    )


@client.route("/delete_testimonial/<int:testimonial_id>", methods=["POST"])
@login_required
def delete_testimonial_client(testimonial_id):
    testimonial = Testimonial.query.get_or_404(testimonial_id)

    # Ensure the testimonial belongs to the current user
    if testimonial.user_id != current_user.id:
        flash("You do not have permission to delete this testimonial.", "danger")
        return redirect(url_for("client.dashboard"))

    # Prevent deletion if already approved by admin
    if testimonial.is_approved:
        flash(
            "This testimonial has already been approved and cannot be deleted.",
            "warning",
        )
        return redirect(url_for("client.dashboard"))

    db.session.delete(testimonial)
    db.session.commit()
    flash("Your testimonial has been deleted!", "success")
    return redirect(url_for("client.dashboard"))


@client.route("/delete_order/<int:order_id>", methods=["POST"])
@login_required
def delete_order(order_id):
    order = Order.query.get_or_404(order_id)

    # Ensure the order belongs to the current user
    if order.client_id != current_user.id:
        flash("You do not have permission to delete this order.", "danger")
        return redirect(url_for("client.dashboard"))

    # Only allow deletion if the order is rejected or expired
    if order.status not in ["rejected", "expired"]:
        flash("Only rejected or expired orders can be deleted.", "danger")
        return redirect(url_for("client.dashboard"))

    # Delete associated CalendarEvent if exists
    if order.calendar_event:
        db.session.delete(order.calendar_event)

    # Delete associated Testimonial if exists
    testimonial = Testimonial.query.filter_by(order_id=order.id).first()
    if testimonial:
        db.session.delete(testimonial)

    db.session.delete(order)
    db.session.commit()
    flash("Order has been deleted successfully!", "success")
    return redirect(url_for("client.dashboard"))


@client.route("/request_cancellation/<int:order_id>", methods=["POST"])
@login_required
def request_cancellation(order_id):
    order = Order.query.get_or_404(order_id)

    if order.client_id != current_user.id:
        flash("Anda tidak memiliki izin untuk membatalkan pesanan ini.", "danger")
        return redirect(url_for("client.dashboard"))

    # Kebijakan pembatalan: DP hangus
    # Informasikan klien sebelum konfirmasi final
    # (Implementasi konfirmasi di frontend)

    order.status = "cancellation_requested"
    order.cancellation_reason = request.form.get(
        "cancellation_reason", "Tidak ada alasan diberikan."
    )
    order.cancellation_requested = True  # Set the flag
    db.session.commit()

    # --- NOTIFIKASI: Permintaan Pembatalan --- #
    admins = User.query.filter_by(role="admin").all()
    for admin_user in admins:
        package_or_service_name = (
            order.wedding_package.name if order.wedding_package else order.service_type
        )
        notification = Notification(
            user_id=admin_user.id,
            type="cancellation_request",
            entity_id=order.id,
            message=(
                f"Permintaan pembatalan pesanan {package_or_service_name} dari "
                f"{current_user.username}."
            ),
        )
        db.session.add(notification)
    db.session.commit()
    # --- END NOTIFIKASI --- #

    flash(
        "Permintaan pembatalan Anda telah diajukan. Admin akan segera meninjaunya.",
        "success",
    )

    # Send email notification to admin
    cancellation_reason_admin = f"Permintaan pembatalan pesanan {order.id} dari {order.client.full_name} telah diajukan. Alasan: {order.cancellation_reason or 'Tidak ada alasan diberikan.'}"
    try:
        send_cancellation_notification_to_admin(order, cancellation_reason_admin)
    except Exception as e:
        current_app.logger.error(f"Failed to send cancellation request notification to admin for order {order.id}: {e}")

    return redirect(url_for("client.dashboard"))


@client.route("/request_reschedule/<int:order_id>", methods=["POST"])
@login_required
def request_reschedule(order_id):
    order = Order.query.get_or_404(order_id)

    if order.client_id != current_user.id:
        flash("Anda tidak memiliki izin untuk menjadwal ulang pesanan ini.", "danger")
        return redirect(url_for("client.dashboard"))

    # Kebijakan: tidak ada biaya tambahan untuk penjadwalan ulang
    # (Informasi ini akan ditampilkan di frontend)

    # Ambil data dari form modal
    new_event_date_str = request.form.get("new_event_date")
    new_event_start_time_str = request.form.get("new_event_start_time")
    new_event_end_time_str = request.form.get("new_event_end_time")
    reschedule_reason = request.form.get(
        "reschedule_reason", "Tidak ada alasan diberikan."
    )

    # Konversi tanggal dan waktu ke objek datetime
    new_event_date = (
        datetime.strptime(new_event_date_str, "%Y-%m-%d").date()
        if new_event_date_str
        else None
    )
    new_start_time = (
        datetime.strptime(new_event_start_time_str, "%H:%M").time()
        if new_event_start_time_str
        else None
    )
    new_end_time = (
        datetime.strptime(new_event_end_time_str, "%H:%M").time()
        if new_event_end_time_str
        else None
    )

    # Gabungkan tanggal dan waktu menjadi objek datetime lengkap
    full_new_start_datetime = (
        datetime.combine(new_event_date, new_start_time)
        if new_event_date and new_start_time
        else None
    )
    full_new_end_datetime = (
        datetime.combine(new_event_date, new_end_time)
        if new_event_date and new_end_time
        else None
    )

    # Periksa ketersediaan slot baru (logika sederhana, bisa diperluas)
    # Asumsi: jika prewedding, tidak perlu cek waktu
    if order.service_type != "prewedding" and (
        not full_new_start_datetime
        or not full_new_end_datetime
    ):
        flash(
            "Mohon lengkapi tanggal dan waktu baru untuk penjadwalan ulang.",
            "danger",
        )
        return redirect(url_for("client.dashboard"))

    # Periksa tumpang tindih dengan event kalender lain (
    # kecuali event order ini sendiri
    # )
    overlapping_event = CalendarEvent.query.filter(
        CalendarEvent.order_id != order.id,  # Exclude current order's event
        (CalendarEvent.start_time < full_new_end_datetime)
        & (CalendarEvent.end_time > full_new_start_datetime),
    ).first()

    if overlapping_event:
        flash(
            "Tanggal dan waktu yang diminta tidak tersedia. Mohon pilih tanggal/waktu "
            "lain.",
            "danger",
        )
        return redirect(url_for("client.dashboard"))

    order.status = "reschedule_requested"
    order.reschedule_reason = reschedule_reason
    order.requested_event_date = new_event_date
    order.requested_start_time = full_new_start_datetime
    order.requested_end_time = full_new_end_datetime
    db.session.commit()

    # --- NOTIFIKASI: Permintaan Penjadwalan Ulang --- #
    admins = User.query.filter_by(role="admin").all()
    for admin_user in admins:
        package_or_service_name = (
            order.wedding_package.name if order.wedding_package else order.service_type
        )
        notification = Notification(
            user_id=admin_user.id,
            type="reschedule_request",
            entity_id=order.id,
            message=(
                f"Permintaan penjadwalan ulang pesanan {package_or_service_name} "
                f"dari {current_user.username}."
            ),
        )
        db.session.add(notification)
    db.session.commit()
    # --- END NOTIFIKASI --- #

    flash(
            "Permintaan penjadwalan ulang Anda telah diajukan. "
            "Admin akan segera meninjaunya.",
            "success",
        )

    # Send email notification to admin
    try:
        send_reschedule_notification_to_admin(
            order,
            new_event_date,
            new_start_time,
            new_end_time,
            reschedule_reason,
            "requested"
        )
    except Exception as e:
        current_app.logger.error(f"Failed to send reschedule request notification to admin for order {order.id}: {e}")

    return redirect(url_for("client.dashboard"))


@client.route("/dp_payment/<int:order_id>", methods=["GET", "POST"])
@login_required
def dp_payment(order_id):
    order = Order.query.get_or_404(order_id)
    form = DPPaymentForm()

    if order.client_id != current_user.id:
        flash("You do not have permission to view this page.", "danger")
        return redirect(url_for("client.dashboard"))

    # Allow payment/re-upload only if status is 'waiting_dp' or 'rejected'
    if order.status not in ["waiting_dp", "rejected"]:
        flash(
            f"This order is not awaiting DP payment (status: {order.status}).",
            "warning",
        )
        return redirect(url_for("client.dashboard"))

    # --- Timeout Logic ---
    time_remaining = None
    deadline = None

    # Get current UTC time (timezone-aware)
    now_utc = datetime.utcnow().replace(tzinfo=pytz.utc)

    if order.status == "waiting_dp":
        # created_at is naive UTC, make it timezone-aware UTC
        created_at_utc = order.created_at.replace(tzinfo=pytz.utc)
        deadline_utc = created_at_utc + timedelta(hours=1)
    elif order.status == "rejected":
        # If rejected, the deadline is 1 hour from rejection timestamp.
        # If dp_rejection_timestamp is somehow None for a rejected order,
        # give a fresh 1-hour window from now to allow re-upload.
        base_time_utc = (
            order.dp_rejection_timestamp
            if order.dp_rejection_timestamp
            else datetime.utcnow()
        ).replace(tzinfo=pytz.utc)
        deadline_utc = base_time_utc + timedelta(hours=1)

    if deadline_utc and now_utc > deadline_utc:
        order.status = "expired"
        db.session.commit()
        flash(
            "This order has expired because the DP was not paid "
            "within the allowed time.",
            "danger",
        )
        return redirect(url_for("client.dashboard"))
    elif deadline_utc:
        time_remaining = deadline_utc - now_utc
        # Convert deadline to Jakarta time for display
        deadline = deadline_utc.astimezone(JAKARTA_TZ)

    # --- Form Processing (moved from pay_dp) ---
    bank_accounts = BankAccount.query.filter_by(is_active=True).all()
    form.bank_account.choices = [
        (str(acc.id), f"{acc.bank_name} - {acc.account_name} ({acc.account_number})")
        for acc in bank_accounts
    ]

    if form.validate_on_submit():
        order.bank_account_id = int(form.bank_account.data)  # Save selected bank account
        if form.payment_proof.data:
            # Save the uploaded file
            filename = secure_filename(form.payment_proof.data.filename)
            upload_folder = os.path.join(
                current_app.root_path, "static", "payment_proofs"
            )
            os.makedirs(upload_folder, exist_ok=True)
            file_path = os.path.join(upload_folder, filename)
            form.payment_proof.data.save(file_path)
            order.dp_payment_proof = filename

        order.dp_paid = order.total_price * 0.15
        order.status = "waiting_approval"
        order.dp_rejection_timestamp = None  # Clear timestamp on new submission
        db.session.commit()
        flash(
            "DP payment proof submitted successfully! Your order is now "
            "awaiting admin approval.",
            "success",
        )
        return redirect(url_for("client.dashboard"))

    # --- Data for Template ---
    dp_amount = order.total_price * 0.15

    package_name = "N/A"
    if order.wedding_package:
        package_name = order.wedding_package.name

    return render_template(
        "client/dp_payment.html",
        order=order,
        dp_amount=dp_amount,
        form=form,
        bank_accounts=bank_accounts,
        time_remaining=time_remaining,
        deadline=deadline,
        package_name=package_name,
    )


@client.route("/client/order/<int:order_id>/view_invoice")
@login_required
def view_invoice_client(order_id):
    order = Order.query.get_or_404(order_id)

    if order.client_id != current_user.id:
        flash("You do not have permission to view this invoice.", "danger")
        return redirect(url_for("client.dashboard"))

    # bank_accounts = BankAccount.query.filter_by(is_active=True).all() # Removed
    return render_template(
        "invoice.html",
        order=order,
        timedelta=timedelta,
        bank_account=order.bank_account,
    )


@client.route("/profile", methods=["GET", "POST"])
@login_required
def edit_profile_client():
    form = UserEditForm(
        original_username=current_user.username, original_email=current_user.email
    )
    if form.validate_on_submit():
        current_user.full_name = form.full_name.data
        current_user.username = form.username.data
        current_user.email = form.email.data
        current_user.whatsapp_number = form.whatsapp_number.data
        if form.password.data:
            current_user.password = generate_password_hash(
                form.password.data, method="pbkdf2:sha256"
            )
        db.session.commit()
        flash("Your profile has been updated successfully!", "success")
        return redirect(url_for("client.dashboard"))
    elif request.method == "GET":
        form.full_name.data = current_user.full_name
        form.username.data = current_user.username
        form.email.data = current_user.email
        form.whatsapp_number.data = current_user.whatsapp_number
    return render_template(
        "edit_profile.html", form=form, user=current_user, title="Edit Client Profile"
    )


@client.route("/api/notifications/mark_read/<int:notification_id>", methods=["POST"])
@login_required
def mark_notification_as_read(notification_id):
    notification = Notification.query.get(notification_id)
    if notification and notification.user_id == current_user.id:
        notification.is_read = True
        db.session.commit()
        return jsonify(success=True)
    return jsonify(success=False), 400
