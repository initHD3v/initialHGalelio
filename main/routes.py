from models import (
    Post,
    Order,
    db,
    CalendarEvent,
    Testimonial,
    WeddingPackage,
    PostImage,
    ImageLike,
    Notification,
    User,
    HomepageContent,
    HeroImage,
)
from flask import (
    render_template,
    redirect,
    url_for,
    flash,
    jsonify,
    request,
)
from datetime import datetime
from forms import OrderForm
from flask_login import login_required, current_user
from sqlalchemy import or_, func
from . import main


@main.route("/")
def index():
    hero_images = HeroImage.query.order_by(HeroImage.order.asc()).all()
    # Calculate total likes for each post and order by it
    # This query will return (Post object, total_likes) tuples
    posts_with_total_likes = (
        db.session.query(Post, func.sum(PostImage.likes).label("total_likes"))
        .join(PostImage)
        .group_by(Post)
        .order_by(func.sum(PostImage.likes).desc())
        .limit(3)
        .all()
    )

    featured_posts = []
    for post, total_likes in posts_with_total_likes:
        post.total_likes = total_likes  # Attach total_likes to the post object
        featured_posts.append(post)
    testimonials = (
        Testimonial.query.filter_by(is_approved=True)
        .order_by(Testimonial.id.desc())
        .limit(3)
        .all()
    )
    homepage_content = HomepageContent.query.first()
    if not homepage_content:
        # Create a default entry if none exists
        homepage_content = HomepageContent(
            about_text="Teks default tentang Aruna Moment.",
            about_image_filename="pp.jpg",
        )
        db.session.add(homepage_content)
        db.session.commit()
    return render_template(
        "index.html",
        hero_images=hero_images,
        featured_posts=featured_posts,
        testimonials=testimonials,
        homepage_content=homepage_content,
    )


@main.route("/about")
def about():
    return render_template("about.html")


@main.route("/portfolio")
def portfolio():
    posts = Post.query.order_by(Post.date_posted.desc()).all()

    if current_user.is_authenticated and current_user.role == "client":
        for post in posts:
            for image in post.images:
                image.is_liked_by_current_user = (
                    ImageLike.query.filter_by(
                        user_id=current_user.id, post_image_id=image.id
                    ).first()
                    is not None
                )
    else:
        # For non-logged-in users or non-clients, set all to False
        for post in posts:
            for image in post.images:
                image.is_liked_by_current_user = False

    return render_template("portfolio.html", posts=posts)


@main.route("/testimonials")
def testimonials():
    testimonials = Testimonial.query.filter_by(is_approved=True).all()
    return render_template("testimonials.html", testimonials=testimonials)


@main.route("/contact")
def contact():
    return render_template("contact.html")


@main.route("/pricelist")
def pricelist():
    packages = WeddingPackage.query.order_by(
        WeddingPackage.category, WeddingPackage.price
    ).all()
    # Group packages by category
    categorized_packages = {}
    for pkg in packages:
        if pkg.category not in categorized_packages:
            categorized_packages[pkg.category] = []
        categorized_packages[pkg.category].append(pkg)
    return render_template("pricelist.html", categorized_packages=categorized_packages)


@main.route("/order", methods=["GET", "POST"])
@login_required
def order():
    if current_user.role == "admin":
        flash("Pengguna admin tidak dapat membuat pesanan.", "danger")
        return redirect(url_for("admin.admin_panel"))
    form = OrderForm()

    # Pre-fill form based on query parameters
    if request.method == "GET":
        service_type = request.args.get("service_type")
        package_id = request.args.get("package_id", type=int)

        if service_type:
            form.service_type.data = service_type

        if package_id:
            package = WeddingPackage.query.get(package_id)
            if package:
                if service_type == "wedding":
                    form.wedding_package.data = package
                elif service_type == "prewedding":
                    form.prewedding_package.data = package

    if form.validate_on_submit():
        requested_date = form.event_date.data
        service_type = form.service_type.data

        full_start_datetime = None
        full_end_datetime = None

        if service_type == "prewedding":
            # For prewedding, set default full-day time
            full_start_datetime = datetime.combine(requested_date, datetime.min.time())
            full_end_datetime = datetime.combine(requested_date, datetime.max.time())
        else:
            # For other services, require time input
            if not form.event_start_time.data or not form.event_end_time.data:
                flash(
                    "Mohon berikan waktu mulai dan berakhir untuk jenis layanan ini.",
                    "danger",
                )
                return render_template("order.html", form=form)
            try:
                start_time_obj = datetime.strptime(
                    form.event_start_time.data, "%H:%M"
                ).time()
                end_time_obj = datetime.strptime(
                    form.event_end_time.data, "%H:%M"
                ).time()
            except (ValueError, TypeError):
                flash("Format waktu tidak valid. Mohon gunakan HH:MM.", "danger")
                return render_template("order.html", form=form)

            full_start_datetime = datetime.combine(requested_date, start_time_obj)
            full_end_datetime = datetime.combine(requested_date, end_time_obj)

        # Check if there's an accepted/completed order or an unavailable
        # calendar event that overlaps (only for services with specific times)
        existing_event = CalendarEvent.query.filter(
            (CalendarEvent.start_time < full_end_datetime)
            & (CalendarEvent.end_time > full_start_datetime),
            or_(not CalendarEvent.is_available, CalendarEvent.order_id.isnot(None)),
        ).first()

        if existing_event:
            flash(
                "Slot tanggal dan waktu ini sudah dipesan atau tidak tersedia. "
                "Mohon pilih waktu lain.",
                "danger",
            )
            return render_template("order.html", form=form)

        # Determine total_price, wedding_package_id, and dp_paid based on service_type
        selected_package = None
        order_total_price = 0.0
        dp_amount = 0.0
        selected_wedding_package_id = None

        if service_type == "wedding":
            if form.wedding_package.data:
                selected_package = form.wedding_package.data
                order_total_price = selected_package.price
                selected_wedding_package_id = selected_package.id
            else:
                flash("Mohon pilih paket Pernikahan.", "danger")
                return render_template("order.html", form=form)
        elif service_type == "prewedding":
            if form.prewedding_package.data:
                selected_package = form.prewedding_package.data
                order_total_price = selected_package.price
                selected_wedding_package_id = selected_package.id
                dp_amount = order_total_price * 0.15  # 15% DP for prewedding
            else:
                flash("Mohon pilih paket Pra-pernikahan.", "danger")
                return render_template("order.html", form=form)
        else:  # For 'event', 'portrait', or other custom services
            if form.total_price.data is None or form.total_price.data <= 0:
                flash(
                    "Mohon masukkan total harga yang valid untuk jenis layanan ini.",
                    "danger",
                )
                return render_template("order.html", form=form)
            order_total_price = form.total_price.data

        order = Order(
            client_id=current_user.id,
            service_type=service_type,
            event_date=requested_date,
            event_start_time=full_start_datetime,
            event_end_time=full_end_datetime,
            location=form.location.data,
            latitude=form.latitude.data if form.latitude.data else None,
            longitude=form.longitude.data if form.longitude.data else None,
            details=form.details.data,
            total_price=order_total_price,
            dp_paid=dp_amount,
            wedding_package_id=selected_wedding_package_id,
            status="waiting_dp",
        )
        db.session.add(order)
        db.session.commit()

        # Create a CalendarEvent for this order and mark it unavailable
        # Only create if start and end times are available
        if full_start_datetime and full_end_datetime:
            calendar_event = CalendarEvent(
                title=f"Booking for {current_user.username}",
                start_time=full_start_datetime,
                end_time=full_end_datetime,
                description=f"Service: {service_type}",
                is_available=False,
                order_id=order.id,
            )
            db.session.add(calendar_event)
            db.session.commit()

        # --- NOTIFICATION: New Order --- #
        admins = User.query.filter_by(role="admin").all()
        for admin_user in admins:
            notification = Notification(
                user_id=admin_user.id,
                type="new_order",
                entity_id=order.id,
                message=(
                    f"Pesanan baru dari {current_user.username} untuk {service_type} "
                    f"pada {requested_date.strftime('%Y-%m-%d')}."
                )
            )
            db.session.add(notification)
            db.session.commit()
