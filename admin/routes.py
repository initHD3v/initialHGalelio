from flask import (
    render_template,
    flash,
    redirect,
    url_for,
    request,
    send_file,
    current_app,
    jsonify,
)
from flask_login import login_required, current_user
from flask_mail import Message
from extensions import mail # Import mail object
from tasks import send_email_task # Import Celery task
from models import (
    Post,
    Order,
    Testimonial,
    CalendarEvent,
    User,
    WeddingPackage,
    BankAccount,
    PostImage,
    ImageLike,
    Notification,
    HomepageContent,
    HeroImage,  # Added HeroImage
)
from forms import (
    PostForm,
    TestimonialForm,
    CalendarEventForm,
    UserEditForm,
    WeddingPackageForm,
    BankAccountForm,
    AdminOrderForm,
    HomepageContentForm,
)
from extensions import db
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename
import os
from datetime import datetime, timedelta, UTC
from flask_babel import _
from sqlalchemy import or_
from . import admin

def send_order_status_email(order):
    try:
        client_name = order.client.full_name
        msg = Message(
            f"Pembaruan Status Pesanan Anda: {order.wedding_package.name if order.wedding_package else (order.prewedding_package.name if order.prewedding_package else order.service_type)}",
            recipients=[order.client.email]
        )
        msg.html = render_template(
            'emails/order_status_update.html',
            order=order,
            client_name=client_name,
            current_year=datetime.now().year
        )
        send_email_task.delay(
            subject=msg.subject,
            sender=msg.sender,
            recipients=msg.recipients,
            body=msg.html # Mengirim HTML sebagai body
        )
    except Exception as e:
        current_app.logger.error(f"Failed to send order status email for order {order.id}: {e}")

def send_payment_rejection_email_to_client(order, rejection_reason):
    try:
        client_name = order.client.full_name
        msg = Message(
            f"Bukti Pembayaran Ditolak untuk Pesanan Anda: {order.wedding_package.name if order.wedding_package else (order.prewedding_package.name if order.prewedding_package else order.service_type)}",
            recipients=[order.client.email]
        )
        msg.html = render_template(
            'emails/order_payment_rejected_client.html',
            order=order,
            client_name=client_name,
            rejection_reason=rejection_reason,
            current_year=datetime.now().year
        )
        send_email_task.delay(
            subject=msg.subject,
            sender=msg.sender,
            recipients=msg.recipients,
            body=msg.html # Mengirim HTML sebagai body
        )
    except Exception as e:
        current_app.logger.error(f"Failed to send payment rejection email to client for order {order.id}: {e}")

def send_cancellation_email_to_client(order, cancellation_reason):
    try:
        client_name = order.client.full_name
        msg = Message(
            f"Pembatalan Pesanan Anda: {order.wedding_package.name if order.wedding_package else (order.prewedding_package.name if order.prewedding_package else order.service_type)}",
            recipients=[order.client.email]
        )
        msg.html = render_template(
            'emails/order_cancellation_client.html',
            order=order,
            client_name=client_name,
            cancellation_reason=cancellation_reason,
            current_year=datetime.now().year
        )
        send_email_task.delay(
            subject=msg.subject,
            sender=msg.sender,
            recipients=msg.recipients,
            body=msg.html # Mengirim HTML sebagai body
        )
    except Exception as e:
        current_app.logger.error(f"Failed to send cancellation email to client for order {order.id}: {e}")

def send_cancellation_notification_to_admin(order, cancellation_reason):
    try:
        admins = User.query.filter_by(role="admin").all()
        for admin_user in admins:
            msg = Message(
                f"Notifikasi Pembatalan Pesanan: {order.wedding_package.name if order.wedding_package else (order.prewedding_package.name if order.prewedding_package else order.service_type)}",
                recipients=[admin_user.email]
            )
            msg.html = render_template(
                'emails/order_cancellation_admin.html',
                order=order,
                cancellation_reason=cancellation_reason,
                current_year=datetime.now().year
            )
            send_email_task.delay(
                subject=msg.subject,
                sender=msg.sender,
                recipients=msg.recipients,
                body=msg.html # Mengirim HTML sebagai body
            )
    except Exception as e:
        current_app.logger.error(f"Failed to send cancellation notification to admin for order {order.id}: {e}")

def send_reschedule_email_to_client(order, new_date, new_start_time, new_end_time, reschedule_reason, status):
    try:
        client_name = order.client.full_name
        msg = Message(
            f"Pembaruan Penjadwalan Ulang Pesanan Anda: {order.wedding_package.name if order.wedding_package else (order.prewedding_package.name if order.prewedding_package else order.service_type)}",
            recipients=[order.client.email]
        )
        msg.html = render_template(
            'emails/order_reschedule_client.html',
            order=order,
            client_name=client_name,
            new_date=new_date,
            new_start_time=new_start_time,
            new_end_time=new_end_time,
            reschedule_reason=reschedule_reason,
            status=status,
            current_year=datetime.now().year
        )
        send_email_task.delay(
            subject=msg.subject,
            sender=msg.sender,
            recipients=msg.recipients,
            body=msg.html # Mengirim HTML sebagai body
        )
    except Exception as e:
        current_app.logger.error(f"Failed to send reschedule email to client for order {order.id}: {e}")

def send_reschedule_notification_to_admin(order, new_date, new_start_time, new_end_time, reschedule_reason, status):
    try:
        admins = User.query.filter_by(role="admin").all()
        for admin_user in admins:
            msg = Message(
                f"Notifikasi Penjadwalan Ulang Pesanan: {order.wedding_package.name if order.wedding_package else (order.prewedding_package.name if order.prewedding_package else order.service_type)}",
                recipients=[admin_user.email]
            )
            msg.html = render_template(
                'emails/order_reschedule_admin.html',
                order=order,
                new_date=new_date,
                new_start_time=new_start_time,
                new_end_time=new_end_time,
                reschedule_reason=reschedule_reason,
                status=status,
                current_year=datetime.now().year
            )
            send_email_task.delay(
                subject=msg.subject,
                sender=msg.sender,
                recipients=msg.recipients,
                body=msg.html # Mengirim HTML sebagai body
            )
    except Exception as e:
        current_app.logger.error(f"Failed to send reschedule notification to admin for order {order.id}: {e}")


@admin.route("/admin/manage_homepage", methods=["GET", "POST"])
@login_required
def manage_homepage():
    if current_user.role != "admin":
        flash(_("You do not have access to this page."), "danger")
        return redirect(url_for("main.index"))

    homepage_content = HomepageContent.query.first()
    if not homepage_content:
        homepage_content = HomepageContent(
            about_text="Teks default tentang Aruna Moment.",
            about_image_filename="pp.jpg",
        )
        db.session.add(homepage_content)
        db.session.commit()

    form = HomepageContentForm(obj=homepage_content)
    hero_images = HeroImage.query.order_by(HeroImage.order.asc()).all()

    # Ensure the directory for hero images exists
    hero_image_dir = os.path.join(current_app.root_path, "static/hero_carousel_images")
    os.makedirs(hero_image_dir, exist_ok=True)

    if form.validate_on_submit():
        # Handle about_text update
        homepage_content.about_text = form.about_text.data

        # Handle about_image upload
        if form.about_image.data:
            image_file = form.about_image.data
            filename = secure_filename(image_file.filename)
            image_path = os.path.join(current_app.root_path, "static/images", filename)
            image_file.save(image_path)
            homepage_content.about_image_filename = filename

        # Handle new hero image uploads
        if form.hero_images.data:
            for hero_image_file in request.files.getlist(form.hero_images.name):
                if hero_image_file.filename:
                    filename = secure_filename(hero_image_file.filename)
                    filepath = os.path.join(hero_image_dir, filename)
                    hero_image_file.save(filepath)
                    new_hero_image = HeroImage(
                        filename=filename, order=len(hero_images) + 1
                    )
                    db.session.add(new_hero_image)

        # Handle existing hero image deletions
        for image in hero_images:
            delete_checkbox_name = f"delete_hero_image_{image.id}"
            if request.form.get(delete_checkbox_name):
                # Delete from filesystem
                filepath = os.path.join(hero_image_dir, image.filename)
                if os.path.exists(filepath):
                    os.remove(filepath)
                # Delete from database
                db.session.delete(image)

        db.session.commit()
        flash(_("Homepage content updated successfully!"), "success")
        return redirect(url_for("admin.manage_homepage"))

    return render_template(
        "admin/manage_homepage.html",
        form=form,
        homepage_content=homepage_content,
        hero_images=hero_images,  # Pass hero_images to template
        title=_("Manage Homepage"),
    )


@admin.route("/admin/upload_hero_image", methods=["POST"])
@login_required
def upload_hero_image():
    if current_user.role != "admin":
        return jsonify({"success": False, "message": "Unauthorized"}), 403

    if 'hero_image' not in request.files:
        return jsonify({"success": False, "message": "No file part"}), 400

    file = request.files['hero_image']

    if file.filename == '':
        return jsonify({"success": False, "message": "No selected file"}), 400

    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
    def allowed_file(filename):
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in allowed_extensions

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        upload_folder = os.path.join(current_app.root_path, 'static', 'images', 'hero_uploads')
        os.makedirs(upload_folder, exist_ok=True)
        file_path = os.path.join(upload_folder, filename)
        file.save(file_path)

        # Update HERO_IMAGE_PATH in config and save to file
        relative_path = os.path.join('images', 'hero_uploads', filename).replace('\\', '/')
        current_app.config['HERO_IMAGE_PATH'] = relative_path

        # Save the new path to a file for persistence
        config_file_path = os.path.join(current_app.root_path, 'instance', 'hero_image_config.txt')
        with open(config_file_path, 'w') as f:
            f.write(relative_path)

        return jsonify({"success": True, "message": "Hero image updated successfully!", "new_image_url": url_for('static', filename=relative_path)}), 200
    else:
        return jsonify({"success": False, "message": "Invalid file type"}), 400


@admin.route("/admin")
@login_required
def admin_panel():
    if current_user.role != "admin":
        flash(_("You do not have access to this page."), "danger")
        return redirect(url_for("main.index"))
    orders = Order.query.all()
    testimonials = Testimonial.query.all()
    # Fetch calendar events for approved orders or unavailable events
    calendar_events = (
        CalendarEvent.query.join(
            Order, CalendarEvent.order_id == Order.id, isouter=True
        )
        .filter(
            or_(
                # Event is for an order that is not completed or rejected
                (Order.status.notin_(["completed", "rejected"])),
                # Event is a manual unavailability block (no order)
                (CalendarEvent.order_id.is_(None) & (not CalendarEvent.is_available)),
            )
        )
        .all()
    )
    # Format events for FullCalendar
    formatted_events = [
        {
            "title": event.title,
            "start": event.start_time.strftime("%Y-%m-%d %H:%M"),
            "end": event.end_time.strftime("%Y-%m-%d %H:%M"),
            "description": event.description,
            "color": (
                "#28a745" if event.order_id else "#dc3545"
            ),  # Green for approved orders, red for unavailable
        }
        for event in calendar_events
    ]

    # Fetch summary statistics
    total_clients = User.query.filter_by(role="client").count()
    total_orders = Order.query.count()
    total_wedding_packages = WeddingPackage.query.count()

    # Fetch upcoming accepted orders for countdown
    upcoming_orders = (
        Order.query.filter(
            Order.status == "accepted",
            Order.event_date >= datetime.now(UTC).date(),  # Only future events
            Order.event_start_time.isnot(None),
        )
        .order_by(Order.event_date.asc())
        .all()
    )

    # Calculate time remaining for each upcoming order
    for order in upcoming_orders:
        # Combine event_date with event_start_time to get full datetime object
        event_datetime = datetime.combine(
            order.event_date, order.event_start_time.time()
        )
        time_remaining = event_datetime - datetime.utcnow()
        order.time_remaining = time_remaining  # Attach to order object
    pending_orders = Order.query.filter_by(status="pending").count()
    approved_orders = Order.query.filter_by(status="approved").count()
    rejected_orders = Order.query.filter_by(status="rejected").count()

    return render_template(
        "admin/dashboard.html",
        orders=orders,
        testimonials=testimonials,
        calendar_events=formatted_events,
        total_clients=total_clients,
        total_orders=total_orders,
        pending_orders=pending_orders,
        approved_orders=approved_orders,
        rejected_orders=rejected_orders,
        total_wedding_packages=total_wedding_packages,
        upcoming_orders=upcoming_orders,
    )


@admin.route("/admin/order/<int:order_id>")
@login_required
def order_detail(order_id):
    if current_user.role != "admin":
        flash("You do not have access to this page.", "danger")
        return redirect(url_for("main.index"))

    order = Order.query.get_or_404(order_id)
    return render_template("admin/order_detail.html", order=order, title="Order Details")


@admin.route("/admin/order/<int:order_id>/edit", methods=["GET", "POST"])
@login_required
def edit_order(order_id):
    if current_user.role != "admin":
        flash("You do not have access to this page.", "danger")
        return redirect(url_for("main.index"))

    order = Order.query.get_or_404(order_id)
    form = AdminOrderForm(obj=order)  # Populate form with existing order data

    if form.validate_on_submit():
        # Update order details from form data
        order.service_type = form.service_type.data
        order.event_date = form.event_date.data
        order.location = form.location.data
        # Convert empty strings for latitude/longitude to None
        order.latitude = float(form.latitude.data) if form.latitude.data else None
        order.longitude = float(form.longitude.data) if form.longitude.data else None
        order.details = form.details.data
        order.total_price = form.total_price.data
        order.status = form.status.data
        order.bank_account = (
            form.bank_account.data
        )  # Assign the selected BankAccount object

        # Handle event start/end times based on service type
        if form.service_type.data == "prewedding":
            order.event_start_time = datetime.combine(
                form.event_date.data, datetime.min.time()
            )
            order.event_end_time = datetime.combine(
                form.event_date.data, datetime.max.time()
            )
        else:
            # Convert string times to datetime objects
            order.event_start_time = datetime.combine(
                form.event_date.data,
                datetime.strptime(form.event_start_time.data, "%H:%M").time(),
            )
            order.event_end_time = datetime.combine(
                form.event_date.data,
                datetime.strptime(form.event_end_time.data, "%H:%M").time(),
            )

        # Handle wedding/prewedding packages
        if form.service_type.data == "wedding":
            order.wedding_package = form.wedding_package.data
            order.prewedding_package = (
                None  # Clear prewedding package if service type changes
            )
        elif form.service_type.data == "prewedding":
            order.prewedding_package = form.prewedding_package.data
            order.wedding_package = (
                None  # Clear wedding package if service type changes
            )
        else:
            order.wedding_package = None
            order.prewedding_package = None

        db.session.commit()
        flash("Order updated successfully!", "success")
        return redirect(url_for("admin.order_list"))

    elif request.method == "GET":
        # For GET request, populate time fields from existing order object
        if order.event_start_time:
            form.event_start_time.data = order.event_start_time.strftime("%H:%M")
        if order.event_end_time:
            form.event_end_time.data = order.event_end_time.strftime("%H:%M")

    return render_template(
        "admin/create_edit_order.html", form=form, order=order, title="Edit Order"
    )


@login_required
def get_dashboard_summary():
    if current_user.role != "admin":
        return jsonify({"message": "Unauthorized"}), 403

    total_clients = User.query.filter_by(role="client").count()
    total_orders = Order.query.count()
    pending_orders = Order.query.filter_by(status="pending").count()
    approved_orders = Order.query.filter_by(status="accepted").count()
    rejected_orders = Order.query.filter_by(status="rejected").count()
    total_wedding_packages = WeddingPackage.query.count()

    upcoming_orders_data = []
    upcoming_orders = (
        Order.query.filter(
            Order.status == "accepted",
            Order.event_date >= datetime.now(UTC).date(),  # Only future events
            Order.event_start_time.isnot(None),
        )
        .order_by(Order.event_date.asc())
        .all()
    )

    for order in upcoming_orders:
        event_datetime = datetime.combine(
            order.event_date, order.event_start_time.time()
        )
        time_remaining = event_datetime - datetime.utcnow()

        # Format time_remaining for JSON
        days = time_remaining.days
        hours = time_remaining.seconds // 3600
        minutes = (time_remaining.seconds % 3600) // 60

        upcoming_orders_data.append(
            {
                "client_name": order.client.full_name,
                "service_type": order.service_type,
                "event_date": order.event_date.strftime("%Y-%m-%d"),
                "event_start_time": order.event_start_time.strftime("%H:%M"),
                "time_remaining": {"days": days, "hours": hours, "minutes": minutes},
            }
        )

    return jsonify(
        {
            "total_clients": total_clients,
            "total_orders": total_orders,
            "pending_orders": pending_orders,
            "approved_orders": approved_orders,
            "rejected_orders": rejected_orders,
            "total_wedding_packages": total_wedding_packages,
            "upcoming_orders": upcoming_orders_data,
        }
    )


@admin.route("/admin/portfolio")
@login_required
def manage_portfolio():
    if current_user.role != "admin":
        flash("You do not have access to this page.", "danger")
        return redirect(url_for("main.index"))

    posts = Post.query.all()

    for post in posts:
        # Calculate total likes for the post
        post.total_likes = sum(image.likes for image in post.images)

        # Collect unique users who liked any image in the post
        liking_users_list = []
        for image in post.images:
            for like in image.image_likes:
                liking_users_list.append(
                    {
                        "username": like.user.username,
                        "timestamp": like.timestamp,  # Pass raw datetime object
                    }
                )
        # Sort by timestamp (newest first) and then by username
        post.liking_users_list = sorted(
            liking_users_list,
            key=lambda x: (x["timestamp"], x["username"]),
            reverse=True,
        )

    return render_template("admin/manage_portfolio.html", posts=posts)


@admin.route("/admin/profile", methods=["GET", "POST"])
@login_required
def edit_profile_admin():
    if current_user.role != "admin":
        flash("You do not have access to this page.", "danger")
        return redirect(url_for("main.index"))

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
        return redirect(url_for("admin.admin_panel"))
    elif request.method == "GET":
        form.full_name.data = current_user.full_name
        form.username.data = current_user.username
        form.email.data = current_user.email
        form.whatsapp_number.data = current_user.whatsapp_number
    return render_template(
        "edit_profile.html", form=form, user=current_user, title="Edit Admin Profile"
    )


@admin.route("/admin/client/<int:user_id>/delete", methods=["POST"])
@login_required
def delete_client(user_id):
    if current_user.role != "admin":
        flash("You do not have permission to perform this action.", "danger")
        return redirect(url_for("main.index"))
    user = User.query.get_or_404(user_id)
    if user.role == "admin":
        flash("Cannot delete an admin user.", "danger")
        return redirect(url_for("admin.client_list"))

    try:
        # Delete associated orders and their related data (
        #     calendar events, payment proofs
        # )
        for order in user.orders:
            if order.dp_payment_proof:
                # Secure the filename before creating the path
                safe_filename = secure_filename(order.dp_payment_proof)
                file_path = os.path.join(
                    current_app.root_path,
                    "static/payment_proofs",
                    safe_filename,
                )
                if os.path.exists(file_path):
                    os.remove(file_path)
            if order.calendar_event:
                db.session.delete(order.calendar_event)
            if order.testimonial_submitted:
                db.session.delete(order.testimonial_submitted)
            db.session.delete(order)

        # Delete associated testimonials (if any are directly linked to user
        # and not via order)
        # Note: With current model, testimonials are linked to order, so this might be
        # redundant if cascade works. However, explicit deletion ensures all
        # related data is handled.
        for testimonial in Testimonial.query.filter_by(user_id=user.id).all():
            db.session.delete(testimonial)

        db.session.delete(user)
        db.session.commit()
        flash("Client and all associated data deleted successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting client: {str(e)}", "danger")
    return redirect(url_for("admin.client_list"))


@admin.route("/admin/clients")
@login_required
def client_list():
    if current_user.role != "admin":
        flash("You do not have access to this page.", "danger")
        return redirect(url_for("main.index"))

    search_query = request.args.get("search", "")

    clients_query = User.query.filter_by(role="client")

    if search_query:
        clients_query = clients_query.filter(
            (User.full_name.ilike(f"%{search_query}%"))
            | (User.username.ilike(f"%{search_query}%"))
            | (User.email.ilike(f"%{search_query}%"))
        )

    clients = clients_query.all()
    return render_template(
        "admin/client_list.html", clients=clients, search_query=search_query
    )


@admin.route("/admin/orders")
@login_required
def order_list():
    if current_user.role != "admin":
        flash("You do not have access to this page.", "danger")
        return redirect(url_for("main.index"))

    search_query = request.args.get("search", "")
    status_filter = request.args.get("status", "")

    orders_query = Order.query.join(User).filter(User.role == "client")

    if search_query:
        orders_query = orders_query.filter(
            (User.username.ilike(f"%{search_query}%"))
            | (User.full_name.ilike(f"%{search_query}%"))
            | (Order.service_type.ilike(f"%{search_query}%"))
            | (Order.location.ilike(f"%{search_query}%"))
        )

    if status_filter and status_filter != "all":
        orders_query = orders_query.filter(Order.status == status_filter)

    orders = orders_query.all()
    return render_template(
        "admin/orders_list.html",
        orders=orders,
        search_query=search_query,
        status_filter=status_filter,
    )


@admin.route("/admin/order/<int:order_id>/delete", methods=["POST"])
@login_required
def delete_order(order_id):
    if current_user.role != "admin":
        flash("You do not have permission to perform this action.", "danger")
        return redirect(url_for("main.index"))
    order = Order.query.get_or_404(order_id)
    try:
        # Delete associated payment proof file if it exists
        if order.dp_payment_proof:
            safe_filename = secure_filename(order.dp_payment_proof)
            file_path = os.path.join(
                current_app.root_path, "static/payment_proofs", safe_filename
            )
            if os.path.exists(file_path):
                os.remove(file_path)
        # Delete associated calendar event if it exists
        if order.calendar_event:
            db.session.delete(order.calendar_event)
        # Delete associated testimonial if it exists
        if order.testimonial_submitted:
            db.session.delete(order.testimonial_submitted)

        db.session.delete(order)
        db.session.commit()
        flash("Order and associated data deleted successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting order: {str(e)}", "danger")
    return redirect(url_for("admin.order_list"))


@admin.route("/admin/order/<int:order_id>/approve", methods=["POST"])
@login_required
def approve_order(order_id):
    if current_user.role != "admin":
        flash("You do not have permission to perform this action.", "danger")
        return redirect(url_for("main.index"))
    order = Order.query.get_or_404(order_id)
    if order.status not in ["waiting_approval", "cancelled"]:
        flash(
            "Order cannot be approved. It is not in waiting_approval or cancelled "
            "status.",
            "danger",
        )
        return redirect(url_for("admin.order_list"))
    order.status = "accepted"
    order.is_notified = False  # Reset notification status
    db.session.commit()
    flash("Order approved successfully!", "success")
    try:
        send_order_status_email(order)
    except Exception as e:
        current_app.logger.error(f"Failed to send order status email for order {order.id}: {e}")
    return redirect(url_for("admin.order_list"))


@admin.route("/admin/order/<int:order_id>/approve_reschedule", methods=["POST"])
@login_required
def approve_reschedule(order_id):
    if current_user.role != "admin":
        flash("You do not have permission to perform this action.", "danger")
        return redirect(url_for("main.index"))
    order = Order.query.get_or_404(order_id)

    if order.status != "reschedule_requested":
        flash("Order is not in 'reschedule_requested' status.", "danger")
        return redirect(url_for("admin.order_list"))

    # Update order status
    order.status = "accepted"  # Or 'rescheduled' if you have that status
    order.is_notified = False  # Reset notification status
    db.session.commit()

    # Create notification for client
    notification = Notification(
        user_id=order.client_id,
        type="reschedule_approved",
        entity_id=order.id,
        message=f"Permintaan penjadwalan ulang pesanan Anda ({order.wedding_package.name if order.wedding_package else order.service_type}) telah disetujui."
    )
    db.session.add(notification)
    db.session.commit()

    flash("Permintaan penjadwalan ulang disetujui!", "success")

    # Send email notification to client
    try:
        send_reschedule_email_to_client(
            order,
            order.requested_event_date,
            order.requested_start_time.time() if order.requested_start_time else None,
            order.requested_end_time.time() if order.requested_end_time else None,
            order.reschedule_reason,
            "approved"
        )
    except Exception as e:
        current_app.logger.error(f"Failed to send reschedule approval email to client for order {order.id}: {e}")

    # Send notification to admin
    try:
        send_reschedule_notification_to_admin(
            order,
            order.requested_event_date,
            order.requested_start_time.time() if order.requested_start_time else None,
            order.requested_end_time.time() if order.requested_end_time else None,
            order.reschedule_reason,
            "approved"
        )
    except Exception as e:
        current_app.logger.error(f"Failed to send reschedule approval notification to admin for order {order.id}: {e}")

    return redirect(url_for("admin.order_list"))


@admin.route("/admin/order/<int:order_id>/reject_reschedule", methods=["POST"])
@login_required
def reject_reschedule(order_id):
    if current_user.role != "admin":
        flash("You do not have permission to perform this action.", "danger")
        return redirect(url_for("main.index"))
    order = Order.query.get_or_404(order_id)

    if order.status != "reschedule_requested":
        flash("Order is not in 'reschedule_requested' status.", "danger")
        return redirect(url_for("admin.order_list"))

    # Update order status
    # Revert to previous status or set to a specific rejected status
    order.status = "accepted"  # Revert to accepted, or set to 'reschedule_rejected'
    order.is_notified = False  # Reset notification status
    db.session.commit()

    # Create notification for client
    notification = Notification(
        user_id=order.client_id,
        type="reschedule_rejected",
        entity_id=order.id,
        message=f"Permintaan penjadwalan ulang pesanan Anda ({order.wedding_package.name if order.wedding_package else order.service_type}) telah ditolak."
    )
    db.session.add(notification)
    db.session.commit()

    flash("Permintaan penjadwalan ulang ditolak!", "success")

    # Send email notification to client
    try:
        send_reschedule_email_to_client(
            order,
            order.requested_event_date,
            order.requested_start_time.time() if order.requested_start_time else None,
            order.requested_end_time.time() if order.requested_end_time else None,
            order.reschedule_reason,
            "rejected"
        )
    except Exception as e:
        current_app.logger.error(f"Failed to send reschedule rejection email to client for order {order.id}: {e}")

    # Send notification to admin
    try:
        send_reschedule_notification_to_admin(
            order,
            order.requested_event_date,
            order.requested_start_time.time() if order.requested_start_time else None,
            order.requested_end_time.time() if order.requested_end_time else None,
            order.reschedule_reason,
            "rejected"
        )
    except Exception as e:
        current_app.logger.error(f"Failed to send reschedule rejection notification to admin for order {order.id}: {e}")

    return redirect(url_for("admin.order_list"))


@admin.route("/admin/order/<int:order_id>/reject", methods=["POST"])
@login_required
def reject_order(order_id):
    if current_user.role != "admin":
        flash("You do not have permission to perform this action.", "danger")
        return redirect(url_for("main.index"))
    order = Order.query.get_or_404(order_id)
    if order.status not in ["waiting_approval", "cancelled"]:
        flash(
            "Order cannot be rejected. It is not in waiting_approval or cancelled "
            "status.",
            "danger",
        )
        return redirect(url_for("admin.order_list"))
    
    rejection_reason = request.form.get("rejection_reason", "Bukti pembayaran tidak sesuai atau tidak valid.")

    order.status = "rejected"
    order.is_notified = False  # Reset notification status
    order.dp_rejection_timestamp = datetime.now(UTC)  # Set rejection timestamp
    # Delete payment proof if exists
    if order.dp_payment_proof:
        safe_filename = secure_filename(order.dp_payment_proof)
        file_path = os.path.join(
            current_app.root_path, "static/payment_proofs", safe_filename
        )
        if os.path.exists(file_path):
            os.remove(file_path)
        order.dp_payment_proof = None  # Clear the proof from DB
    db.session.commit()
    flash("Order rejected successfully!", "success")

    try:
        send_payment_rejection_email_to_client(order, rejection_reason)
    except Exception as e:
        current_app.logger.error(f"Failed to send payment rejection email to client for order {order.id}: {e}")

    return redirect(url_for("admin.order_list"))


@admin.route("/admin/order/<int:order_id>/approve_cancellation", methods=["POST"])
@login_required
def approve_cancellation(order_id):
    if current_user.role != "admin":
        flash("You do not have permission to perform this action.", "danger")
        return redirect(url_for("main.index"))
    order = Order.query.get_or_404(order_id)
    if order.cancellation_requested:
        # Delete associated calendar event first
        if order.calendar_event:
            db.session.delete(order.calendar_event)

        order.status = "cancelled"
        order.cancellation_requested = False  # Clear the flag
        order.is_notified = False  # Reset notification status
        db.session.commit()
        flash("Order cancellation approved and calendar slot released!", "success")

        # Send email notification to client
        cancellation_reason_client = "Pembatalan pesanan Anda telah disetujui. Mohon diperhatikan bahwa DP tidak dapat dikembalikan (hangus) sesuai kebijakan pembatalan. Untuk informasi lebih lanjut, silakan hubungi admin via WhatsApp di +6285740109107."
        try:
            send_cancellation_email_to_client(order, cancellation_reason_client)
        except Exception as e:
            current_app.logger.error(f"Failed to send cancellation approval email to client for order {order.id}: {e}")

        # Send notification to admin
        cancellation_reason_admin = f"Pesanan {order.id} dari {order.client.full_name} telah dibatalkan. Alasan: {order.cancellation_reason or 'Tidak ada alasan diberikan.'}"
        try:
            send_cancellation_notification_to_admin(order, cancellation_reason_admin)
        except Exception as e:
            current_app.logger.error(f"Failed to send cancellation approval notification to admin for order {order.id}: {e}")

        # Create notification for client
        client_user = order.client
        package_or_service_name = (
            order.wedding_package.name if order.wedding_package else order.service_type
        )
        notification_message = (
            f"Pembatalan pesanan {package_or_service_name} Anda telah disetujui. "
            f"Mohon diperhatikan bahwa DP tidak dapat dikembalikan (hangus) "
            f"sesuai kebijakan pembatalan. Untuk informasi lebih lanjut, "
            f"silakan hubungi admin via WhatsApp di +6285740109107."
        )
        notification = Notification(
            user_id=client_user.id,
            type="cancellation_approved",
            entity_id=order.id,
            message=notification_message,
        )
        db.session.add(notification)
        db.session.commit()

        

    else:
        flash("No cancellation request found for this order.", "warning")
    return redirect(url_for("admin.order_list"))


@admin.route("/admin/order/<int:order_id>/reject_cancellation", methods=["POST"])
@login_required
def reject_cancellation(order_id):
    if current_user.role != "admin":
        flash("You do not have permission to perform this action.", "danger")
        return redirect(url_for("main.index"))
    order = Order.query.get_or_404(order_id)
    if order.cancellation_requested:
        # Revert status to previous state, assuming 'accepted' or 'pending'
        # You might need to store the previous status if more complex logic is needed
        if (
            order.status == "waiting_cancellation_approval"
        ):  # Assuming this is the status when cancellation is requested
            order.status = "accepted"  # Or whatever the previous status was
        order.cancellation_requested = False  # Clear the flag
        order.is_notified = False  # Reset notification status
        db.session.commit()
        flash("Order cancellation request rejected. Order status reverted.", "success")

        # Send email notification to client
        cancellation_reason_client = "Permintaan pembatalan pesanan Anda telah ditolak. Pesanan Anda tidak dapat dibatalkan kembali. Untuk informasi lebih lanjut, silakan hubungi admin via WhatsApp di +6285740109107."
        try:
            send_cancellation_email_to_client(order, cancellation_reason_client)
        except Exception as e:
            current_app.logger.error(f"Failed to send cancellation rejection email to client for order {order.id}: {e}")

        # Send notification to admin
        cancellation_reason_admin = f"Permintaan pembatalan pesanan {order.id} dari {order.client.full_name} telah ditolak."
        try:
            send_cancellation_notification_to_admin(order, cancellation_reason_admin)
        except Exception as e:
            current_app.logger.error(f"Failed to send cancellation rejection notification to admin for order {order.id}: {e}")

        # Create notification for client
        client_user = order.client
        package_or_service_name = (
            order.wedding_package.name if order.wedding_package else order.service_type
        )
        notification_message = (
            f"Permintaan pembatalan pesanan {package_or_service_name} Anda telah "
            f"ditolak. Pesanan Anda tidak dapat dibatalkan kembali. Untuk "
            f"informasi lebih lanjut, silakan hubungi admin via WhatsApp di "
            f"+6285740109107."
        )
        notification = Notification(
            user_id=client_user.id,
            type="cancellation_rejected",
            entity_id=order.id,
            message=notification_message,
        )
        db.session.add(notification)
        db.session.commit()

    else:
        flash("No cancellation request found for this order.", "warning")
    return redirect(url_for("admin.order_list"))


@admin.route("/admin/order/<int:order_id>/download_ics")
@login_required
def download_ics(order_id):
    if current_user.role != "admin":
        flash("You do not have permission to perform this action.", "danger")
        return redirect(url_for("main.index"))

    order = Order.query.get_or_404(order_id)

    if not order.event_start_time or not order.event_end_time:
        flash(
            "Cannot generate ICS file because event start or end time is not set.",
            "danger",
        )
        return redirect(url_for("admin.order_list"))

    # Format dates for iCalendar
    dtstart = order.event_start_time.strftime("%Y%m%dT%H%M%S")
    dtend = order.event_end_time.strftime("%Y%m%dT%H%M%S")

    # Create iCalendar content
    ics_content = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Your Photography Portfolio//NONSGML v1.0//EN
"
        f"BEGIN:VEVENT
UID:{order.id}@yourportfolio.com
"
        f"DTSTAMP:{datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")}"
"
        f"DTSTART:{dtstart}
DTEND:{dtend}
"
        f"SUMMARY:Photo Session for {order.client.full_name} "
        f"({order.service_type.capitalize()})
"
        f"LOCATION:{order.location}
"
        f"DESCRIPTION:Details: {order.details or 'N/A'}. Client WhatsApp: "
        f"{order.client.whatsapp_number}
END:VEVENT
END:VCALENDAR"""

    # Create a temporary file to serve
    from io import BytesIO

    buffer = BytesIO()
    buffer.write(ics_content.encode("utf-8"))
    buffer.seek(0)

    return send_file(
        buffer,
        mimetype="text/calendar",
        as_attachment=True,
        download_name=f"order_{order.id}_event.ics",
    )


@admin.route("/admin/order/<int:order_id>/complete", methods=["POST"])
@login_required
def mark_order_completed(order_id):
    if current_user.role != "admin":
        flash("You do not have permission to perform this action.", "danger")
        return redirect(url_for("main.index"))
    order = Order.query.get_or_404(order_id)
    order.status = "completed"
    order.can_submit_testimonial = True  # Allow testimonial submission
    order.is_notified = False  # Reset notification status for client
    db.session.commit()
    flash("Order marked as completed and testimonial submission enabled!", "success")
    return redirect(url_for("admin.order_list"))


@admin.route("/admin/portfolio/new", methods=["GET", "POST"])
@login_required
def new_portfolio_post():
    form = PostForm()
    if request.method == "POST":
        # Validasi jumlah file
        images = request.files.getlist("image")
        if (
            not images or not images[0].filename
        ):  # Check if any file is actually uploaded
            return (
                jsonify(
                    {"success": False, "message": "Please upload at least one image."}
                ),
                400,
            )

        if not (1 <= len(images) <= 10):
            return (
                jsonify(
                    {
                        "success": False,
                        "message": "Please upload between 1 and 10 images.",
                    }
                ),
                400,
            )

        post = Post(
            title=request.form.get("title"), content=request.form.get("content")
        )
        db.session.add(post)
        db.session.commit()  # Commit here to get post.id

        for image_file in images:
            if image_file:
                filename = secure_filename(image_file.filename)
                image_path = os.path.join(
                    current_app.root_path, "static/images", filename
                )
                image_file.save(image_path)
                post_image = PostImage(post_id=post.id, filename=filename)
                db.session.add(post_image)
        db.session.commit()

        return jsonify(
            {
                "success": True,
                "message": "Your post has been created!",
                "redirect_url": url_for("admin.manage_portfolio"),
            }
        )

    return render_template(
        "admin_post_form.html", form=form, title="New Portfolio Post"
    )


@admin.route("/admin/portfolio/<int:post_id>/edit", methods=["GET", "POST"])
@login_required
def edit_portfolio_post(post_id):
    post = Post.query.get_or_404(post_id)
    form = PostForm()
    if request.method == "POST":
        # Handle new image uploads
        new_images = request.files.getlist("image")
        uploaded_new_images = [img for img in new_images if img.filename != ""]

        # Validate total number of images after potential deletions and new uploads
        # Need to re-query post.images to get updated list after deletions
        post = Post.query.get_or_404(post_id)  # Re-query to get updated images list
        current_image_count = len(post.images)

        if uploaded_new_images:
            if not (1 <= (current_image_count + len(uploaded_new_images)) <= 10):
                db.session.rollback()
                return (
                    jsonify(
                        {
                            "success": False,
                            "message": "Total images (existing + new) must be "
                            "between 1 and 10.",
                        }
                    ),
                    400,
                )

            for image_file in uploaded_new_images:
                filename = secure_filename(image_file.filename)
                image_path = os.path.join(
                    current_app.root_path, "static/images", filename
                )
                image_file.save(image_path)
                post_image = PostImage(post_id=post.id, filename=filename)
                db.session.add(post_image)
            db.session.commit()

        # If no new images are uploaded and all existing images are marked for deletion
        if not uploaded_new_images and not post.images:
            db.session.rollback()  # Rollback any deletions if this condition is met
            return (
                jsonify(
                    {
                        "success": False,
                        "message": "A post must have at least one image. "
                        "Please upload new images or uncheck delete for existing ones.",
                    }
                ),
                400,
            )

        post.title = request.form.get("title")
        post.content = request.form.get("content")
        db.session.commit()

        return jsonify(
            {
                "success": True,
                "message": "Your post has been updated!",
                "redirect_url": url_for("admin.manage_portfolio"),
            }
        )

    elif request.method == "GET":
        form.title.data = post.title
        form.content.data = post.content
    return render_template(
        "admin_post_form.html", form=form, title="Edit Portfolio Post", post=post
    )


@admin.route("/admin/portfolio/image/<int:image_id>/delete", methods=["POST"])
@login_required
def delete_portfolio_image(image_id):
    if current_user.role != "admin":
        return jsonify({"success": False, "message": "Unauthorized"}), 403

    image_to_delete = PostImage.query.get(image_id)
    if not image_to_delete:
        return jsonify({"success": False, "message": "Image not found"}), 404

    try:
        # Ensure there's at least one image remaining if this is the last one
        post = image_to_delete.post
        if len(post.images) == 1:
            return jsonify({"success": False, "message": "A post must have at least one image."}), 400

        # Delete from filesystem
        safe_filename = secure_filename(image_to_delete.filename)
        image_path = os.path.join(current_app.root_path, "static/images", safe_filename)
        if os.path.exists(image_path):
            os.remove(image_path)

        # Delete from database
        db.session.delete(image_to_delete)
        db.session.commit()
        return jsonify({"success": True, "message": "Image deleted successfully!"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"Error deleting image: {str(e)}"}), 500


@admin.route("/admin/portfolio/<int:post_id>/delete", methods=["POST"])
@login_required
def delete_portfolio_post(post_id):
    post = Post.query.get_or_404(post_id)
    # Delete associated images from filesystem
    for image in post.images:
        safe_filename = secure_filename(image.filename)
        image_path = os.path.join(current_app.root_path, "static/images", safe_filename)
        if os.path.exists(image_path):
            os.remove(image_path)
    db.session.delete(post)  # Cascade delete will handle PostImage entries
    db.session.commit()
    flash("Your post has been deleted!", "success")
    return redirect(url_for("admin.manage_portfolio"))


@admin.route("/admin/calendar")
@login_required
def calendar():
    if current_user.role != "admin":
        flash("You do not have access to this page.", "danger")
        return redirect(url_for("main.index"))
    calendar_events = CalendarEvent.query.all()
    formatted_events = [
        {
            "title": event.title,
            "start": event.start_time.strftime(
                "%Y-%m-%dT%H:%M:%S"
            ),  # ISO 8601 format for FullCalendar
            "end": event.end_time.strftime(
                "%Y-%m-%dT%H:%M:%S"
            ),  # ISO 8601 format for FullCalendar
            "description": event.description,
            "color": (
                "#28a745" if event.order_id else "#dc3545"
            ),  # Green for approved orders, red for unavailable
            "id": event.id,  # Pass event ID for editing/deleting
        }
        for event in calendar_events
    ]
    return render_template("admin/calendar.html", events=formatted_events)


@admin.route("/admin/calendar/new", methods=["GET", "POST"])
@login_required
def new_calendar_event():
    form = CalendarEventForm()
    if form.validate_on_submit():
        event = CalendarEvent(
            title=form.title.data,
            start_time=form.start_time.data,
            end_time=form.end_time.data,
            description=form.description.data,
            is_available=form.is_available.data,
        )
        db.session.add(event)
        db.session.commit()
        flash("Calendar event has been created!", "success")
        return redirect(url_for("admin.calendar"))
    return render_template(
        "admin/create_edit_calendar_event.html", form=form, title="New Calendar Event"
    )


@admin.route("/admin/calendar/<int:event_id>/edit", methods=["GET", "POST"])
@login_required
def edit_calendar_event(event_id):
    event = CalendarEvent.query.get_or_404(event_id)
    form = CalendarEventForm()
    if form.validate_on_submit():
        event.title = form.title.data
        event.start_time = form.start_time.data
        event.end_time = form.end_time.data
        event.description = form.description.data
        event.is_available = form.is_available.data
        db.session.commit()
        flash("Calendar event has been updated!", "success")
        return redirect(url_for("admin.calendar"))
    elif request.method == "GET":
        form.title.data = event.title
        form.start_time.data = event.start_time
        form.end_time.data = event.end_time
        form.description.data = event.description
        form.is_available.data = event.is_available
    return render_template(
        "admin/create_edit_calendar_event.html", form=form, title="Edit Calendar Event"
    )


@admin.route("/admin/calendar/<int:event_id>/delete", methods=["POST"])
@login_required
def delete_calendar_event(event_id):
    event = CalendarEvent.query.get_or_404(event_id)
    db.session.delete(event)
    db.session.commit()
    flash("Calendar event has been deleted!", "success")
    return redirect(url_for("admin.calendar"))


@admin.route("/admin/testimonials")
@login_required
def testimonials_admin():
    testimonials = Testimonial.query.all()
    return render_template("admin/testimonials.html", testimonials=testimonials)


@admin.route("/admin/testimonials/new", methods=["GET", "POST"])
@login_required
def new_testimonial():
    form = TestimonialForm()
    if form.validate_on_submit():
        testimonial = Testimonial(
            client_name=form.client_name.data,
            testimonial_text=form.testimonial_text.data,
            rating=form.rating.data,
            is_approved=form.is_approved.data,
        )
        db.session.add(testimonial)
        db.session.commit()
        flash("Testimonial has been created!", "success")
        return redirect(url_for("admin.testimonials_admin"))
    return render_template(
        "admin/create_edit_testimonial.html", form=form, title="New Testimonial"
    )


@admin.route("/admin/testimonials/<int:testimonial_id>/edit", methods=["GET", "POST"])
@login_required
def edit_testimonial(testimonial_id):
    testimonial = Testimonial.query.get_or_404(testimonial_id)
    form = TestimonialForm()
    if form.validate_on_submit():
        testimonial.client_name = form.client_name.data
        testimonial.testimonial_text = form.testimonial_text.data
        testimonial.rating = form.rating.data
        testimonial.is_approved = form.is_approved.data
        db.session.commit()
        flash("Testimonial has been updated!", "success")
        return redirect(url_for("admin.testimonials_admin"))
    elif request.method == "GET":
        form.client_name.data = testimonial.client_name
        form.testimonial_text.data = testimonial.testimonial_text
        form.rating.data = testimonial.rating
        form.is_approved.data = testimonial.is_approved
    return render_template(
        "admin/create_edit_testimonial.html", form=form, title="Edit Testimonial"
    )


@admin.route("/admin/testimonials/<int:testimonial_id>/delete", methods=["POST"])
@login_required
def delete_testimonial(testimonial_id):
    testimonial = Testimonial.query.get_or_404(testimonial_id)
    db.session.delete(testimonial)
    db.session.commit()
    flash("Testimonial has been deleted!", "success")
    return redirect(url_for("admin.testimonials_admin"))


@admin.route("/admin/testimonials/<int:testimonial_id>/approve", methods=["POST"])
@login_required
def approve_testimonial(testimonial_id):
    if current_user.role != "admin":
        flash("You do not have permission to perform this action.", "danger")
        return redirect(url_for("main.index"))
    testimonial = Testimonial.query.get_or_404(testimonial_id)
    testimonial.is_approved = True
    db.session.commit()
    flash("Testimonial approved successfully!", "success")
    return redirect(url_for("admin.testimonials_admin"))


@admin.route("/admin/testimonials/<int:testimonial_id>/reject", methods=["POST"])
@login_required
def reject_testimonial(testimonial_id):
    if current_user.role != "admin":
        flash("You do not have permission to perform this action.", "danger")
        return redirect(url_for("main.index"))
    testimonial = Testimonial.query.get_or_404(testimonial_id)
    testimonial.is_approved = False
    db.session.commit()
    flash("Testimonial rejected successfully!", "success")
    return redirect(url_for("admin.testimonials_admin"))


# Bank Account Routes
@admin.route("/admin/bank_accounts")
@login_required
def bank_account_list():

    if current_user.role != "admin":
        flash("You do not have access to this page.", "danger")
        return redirect(url_for("main.index"))
    accounts = BankAccount.query.all()
    print(f"DEBUG: Accounts fetched: {accounts}")
    return render_template("admin/bank_accounts.html", accounts=accounts)


from sqlalchemy.exc import IntegrityError  # Added import


@admin.route("/admin/bank_accounts/new", methods=["GET", "POST"])
@login_required
def new_bank_account():
    if current_user.role != "admin":
        flash("You do not have access to this page.", "danger")
        return redirect(url_for("main.index"))
    form = BankAccountForm()
    print(f"DEBUG: Form created: {form}")
    if form.validate_on_submit():
        print(f"DEBUG: Form is submitted and valid.")
        print(f"DEBUG: Form errors: {form.errors}")
        try:
            account = BankAccount(
                bank_name=form.bank_name.data,
                account_number=form.account_number.data,
                account_name=form.account_name.data,
                is_active=form.is_active.data,
            )
            db.session.add(account)
            db.session.commit()
            flash("Bank account created successfully!", "success")
            return redirect(url_for("admin.bank_account_list"))
        except IntegrityError:
            db.session.rollback()
            flash(
                "Nomor Rekening ini sudah terdaftar. Mohon gunakan nomor lain.",
                "danger",
            )
    return render_template(
        "admin/create_edit_bank_account.html", form=form, title="New Bank Account"
    )


@admin.route("/admin/bank_accounts/<int:account_id>/edit", methods=["GET", "POST"])
@login_required
def edit_bank_account(account_id):
    if current_user.role != "admin":
        flash("You do not have access to this page.", "danger")
        return redirect(url_for("main.index"))
    account = BankAccount.query.get_or_404(account_id)
    form = BankAccountForm()
    if form.validate_on_submit():
        account.bank_name = form.bank_name.data
        account.account_number = form.account_number.data
        account.account_name = form.account_name.data
        account.is_active = form.is_active.data
        db.session.commit()
        flash("Bank account updated successfully!", "success")
        return redirect(url_for("admin.bank_account_list"))
    elif request.method == "GET":
        form.bank_name.data = account.bank_name
        form.account_number.data = account.account_number
        form.account_name.data = account.account_name
        form.is_active.data = account.is_active
    return render_template(
        "admin/create_edit_bank_account.html",
        form=form,
        title="Edit Bank Account",
    )


@admin.route("/admin/bank_accounts/<int:account_id>/delete", methods=["POST"])
@login_required
def delete_bank_account(account_id):
    if current_user.role != "admin":
        flash("You do not have permission to perform this action.", "danger")
        return redirect(url_for("main.index"))
    account = BankAccount.query.get_or_404(account_id)
    db.session.delete(account)
    db.session.commit()
    flash("Bank account deleted successfully!", "success")
    return redirect(url_for("admin.bank_account_list"))


@admin.route("/admin/order/<int:order_id>/view_invoice")
@login_required
def view_invoice_admin(order_id):
    if current_user.role != "admin":
        flash("You do not have permission to perform this action.", "danger")
        return redirect(url_for("main.index"))

    order = Order.query.get_or_404(order_id)
    # bank_accounts = BankAccount.query.filter_by(is_active=True).all() # Removed
    return render_template(
        "invoice.html",
        order=order,
        timedelta=timedelta,
        bank_account=order.bank_account,
    )


@admin.route("/admin/wedding_packages")
@login_required
def wedding_package_list():
    if current_user.role != "admin":
        flash("You do not have access to this page.", "danger")
        return redirect(url_for("main.index"))
    packages = WeddingPackage.query.all()
    return render_template("admin/wedding_packages.html", packages=packages)


@admin.route("/admin/wedding_packages/new", methods=["GET", "POST"])
@login_required
def new_wedding_package():
    if current_user.role != "admin":
        flash("You do not have access to this page.", "danger")
        return redirect(url_for("main.index"))
    form = WeddingPackageForm()
    if form.validate_on_submit():
        package = WeddingPackage(
            name=form.name.data,
            description=form.description.data,
            price=form.price.data,
            category=form.category.data,
        )
        db.session.add(package)
        db.session.commit()
        flash("Wedding package created successfully!", "success")
        return redirect(url_for("admin.wedding_package_list"))
    return render_template(
        "admin/create_edit_wedding_package.html", form=form, title="Tambah Paket Baru"
    )


@admin.route("/admin/wedding_packages/<int:package_id>/edit", methods=["GET", "POST"])
@login_required
def edit_wedding_package(package_id):
    if current_user.role != "admin":
        flash("You do not have access to this page.", "danger")
        return redirect(url_for("main.index"))
    package = WeddingPackage.query.get_or_404(package_id)
    form = WeddingPackageForm()
    if form.validate_on_submit():
        package.name = form.name.data
        package.description = form.description.data
        package.price = form.price.data
        package.category = form.category.data
        db.session.commit()
        flash("Wedding package updated successfully!", "success")
        return redirect(url_for("admin.wedding_package_list"))
    elif request.method == "GET":
        form.name.data = package.name
        form.description.data = package.description
        form.price.data = package.price
        form.category.data = package.category
    return render_template(
        "admin/create_edit_wedding_package.html",
        form=form,
        title="Edit Wedding Package",
    )


@admin.route("/admin/wedding_packages/<int:package_id>/delete", methods=["POST"])
@login_required
def delete_wedding_package(package_id):
    if current_user.role != "admin":
        flash("You do not have access to this page.", "danger")
        return redirect(url_for("main.index"))
    package = WeddingPackage.query.get_or_404(package_id)
    db.session.delete(package)
    db.session.commit()
    flash("Wedding package deleted successfully!", "success")
    return redirect(url_for("admin.wedding_package_list"))


# API Endpoints for Notifications
@admin.route("/api/notifications/unread_count")
@login_required
def get_unread_notifications_count():
    if current_user.role != "admin":
        return jsonify({"count": 0}), 403
    count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    return jsonify({"count": count})


@admin.route("/api/notifications")
@login_required
def get_notifications():
    if current_user.role != "admin":
        return jsonify({"notifications": []}), 403

    notifications = (
        Notification.query.filter_by(user_id=current_user.id, is_read=False)
        .order_by(Notification.timestamp.desc())
        .limit(10)
        .all()
    )

    formatted_notifications = []
    for notif in notifications:
        formatted_notifications.append(
            {
                "id": notif.id,
                "type": notif.type,
                "message": notif.message,
                "timestamp": notif.timestamp,  # Pass raw datetime object
                "is_read": notif.is_read,
            }
        )
    return jsonify({"notifications": formatted_notifications})


@admin.route("/api/notifications/mark_read/<int:notification_id>", methods=["POST"])
@login_required
def mark_notification_read(notification_id):
    if current_user.role != "admin":
        return jsonify({"success": False}), 403

    notification = Notification.query.get_or_404(notification_id)
    if notification.user_id != current_user.id:
        return (
            jsonify({"success": False}),
            403,
        )  # Ensure admin can only mark their own notifications as read

    notification.is_read = True
    db.session.commit()
    return jsonify({"success": True})
