from flask import (
    render_template,
    flash,
    redirect,
    url_for,
    request,
    send_file,
    current_app,  # Added
    jsonify,  # Added
)
from flask_login import login_required, current_user
from models import (
    Post,
    Order,
    Testimonial,
    CalendarEvent,
    User,
    WeddingPackage,
    PostImage,  # Added PostImage
)
from forms import (
    PostForm,
    TestimonialForm,
    CalendarEventForm,
    UserEditForm,
    WeddingPackageForm,
)
from extensions import db
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash
import os
from datetime import datetime  # timedelta removed
from . import admin


@admin.route("/admin")
@login_required
def admin_panel():
    if current_user.role != "admin":
        flash("You do not have access to this page.", "danger")
        return redirect(url_for("main.index"))
    orders = Order.query.all()
    testimonials = Testimonial.query.all()
    # Fetch calendar events for approved orders or unavailable events
    calendar_events = CalendarEvent.query.filter(
        (CalendarEvent.order_id.isnot(None)) | (not CalendarEvent.is_available)
    ).all()
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
            Order.event_date >= datetime.utcnow().date(),  # Only future events
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
        "admin.html",
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


@admin.route("/admin/manage_portfolio")
@login_required
def manage_portfolio():
    if current_user.role != "admin":
        flash("You do not have access to this page.", "danger")
        return redirect(url_for("main.index"))
    posts = Post.query.all()
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
                file_path = os.path.join(
                    current_app.root_path,
                    "static/payment_proofs",
                    order.dp_payment_proof,
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
            file_path = os.path.join(
                current_app.root_path, "static/payment_proofs", order.dp_payment_proof
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
    order.status = "rejected"
    order.is_notified = False  # Reset notification status
    # Delete payment proof if exists
    if order.dp_payment_proof:
        file_path = os.path.join(
            current_app.root_path, "static/payment_proofs", order.dp_payment_proof
        )
        if os.path.exists(file_path):
            os.remove(file_path)
        order.dp_payment_proof = None  # Clear the proof from DB
    db.session.commit()
    flash("Order rejected successfully!", "success")
    return redirect(url_for("admin.order_list"))


@admin.route("/admin/order/<int:order_id>/download_ics")
@login_required
def download_ics(order_id):
    if current_user.role != "admin":
        flash("You do not have permission to perform this action.", "danger")
        return redirect(url_for("main.index"))

    order = Order.query.get_or_404(order_id)

    # Format dates for iCalendar
    dtstart = order.event_start_time.strftime("%Y%m%dT%H%M%S")
    dtend = order.event_end_time.strftime("%Y%m%dT%H%M%S")

    # Create iCalendar content
    ics_content = (
        f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Your Photography Portfolio//NONSGML v1.0//EN
"
        f"BEGIN:VEVENT
UID:{order.id}@yourportfolio.com
"
        f"DTSTAMP:{datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")}
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
    )

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
                jsonify({"success": False,
                         "message": "Please upload at least one image."}),
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
        # Handle image deletions
        images_to_delete_ids = request.form.getlist("delete_images")
        for img_id in images_to_delete_ids:
            image_to_delete = PostImage.query.get(img_id)
            if image_to_delete:
                # Delete from filesystem
                image_path = os.path.join(
                    current_app.root_path, "static/images", image_to_delete.filename
                )
                if os.path.exists(image_path):
                    os.remove(image_path)
                # Delete from database
                db.session.delete(image_to_delete)
        db.session.commit()

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


@admin.route("/admin/portfolio/<int:post_id>/delete", methods=["POST"])
@login_required
def delete_portfolio_post(post_id):
    post = Post.query.get_or_404(post_id)
    # Delete associated images from filesystem
    for image in post.images:
        image_path = os.path.join(
            current_app.root_path, "static/images", image.filename
        )
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


# Wedding Packages Routes
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
        )
        db.session.add(package)
        db.session.commit()
        flash("Wedding package created successfully!", "success")
        return redirect(url_for("admin.wedding_package_list"))
    return render_template(
        "admin/create_edit_wedding_package.html", form=form, title="New Wedding Package"
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
        db.session.commit()
        flash("Wedding package updated successfully!", "success")
        return redirect(url_for("admin.wedding_package_list"))
    elif request.method == "GET":
        form.name.data = package.name
        form.description.data = package.description
        form.price.data = package.price
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
