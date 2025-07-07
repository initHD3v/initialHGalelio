from flask import (
    render_template,
    redirect,
    url_for,
    flash,
    jsonify,
)
from datetime import datetime
from models import Post, Order, db, CalendarEvent, Testimonial, WeddingPackage
from forms import OrderForm
from flask_login import login_required, current_user
from sqlalchemy import or_
from . import main
from . import main


@main.route("/")
def index():
    posts = Post.query.all()
    return render_template("index.html", posts=posts)


@main.route("/about")
def about():
    return render_template("about.html")


@main.route("/portfolio")
def portfolio():
    posts = Post.query.all()
    return render_template("portfolio.html", posts=posts)


@main.route("/testimonials")
def testimonials():
    testimonials = Testimonial.query.filter_by(is_approved=True).all()
    return render_template("testimonials.html", testimonials=testimonials)


@main.route("/contact")
def contact():
    return render_template("contact.html")


@main.route("/order", methods=["GET", "POST"])
@login_required
def order():
    if current_user.role == "admin":
        flash("Admin users cannot place orders.", "danger")
        return redirect(url_for("admin.admin_panel"))
    form = OrderForm()
    wedding_packages_list = WeddingPackage.query.all()  # Fetch all wedding packages
    wedding_packages = {
        pkg.id: pkg.price for pkg in wedding_packages_list
    }  # Convert to dict for JS

    if form.validate_on_submit():
        # Backend validation for date availability
        requested_date = form.event_date.data
        try:
            start_time_obj = datetime.strptime(
                form.event_start_time.data, "%H:%M"
            ).time()
            end_time_obj = datetime.strptime(form.event_end_time.data, "%H:%M").time()
        except ValueError:
            flash("Invalid time format. Please use HH:MM.", "danger")
            return render_template(
                "order.html", form=form, wedding_packages=wedding_packages
            )

        # Combine date with start/end times for full datetime objects
        full_start_datetime = datetime.combine(requested_date, start_time_obj)
        full_end_datetime = datetime.combine(requested_date, end_time_obj)

        # Check if there's an accepted/completed order or an unavailable
        # calendar event that overlaps
        existing_event = CalendarEvent.query.filter(
            (CalendarEvent.start_time < full_end_datetime)
            & (CalendarEvent.end_time > full_start_datetime),
            or_(not CalendarEvent.is_available, CalendarEvent.order_id.isnot(None)),
        ).first()

        if existing_event:
            flash(
                "This date and time slot is already booked or unavailable. "
                "Please choose another time.",
                "danger",
            )
            return render_template(
                "order.html", form=form, wedding_packages=wedding_packages
            )

        # Determine total_price and wedding_package_id based on service_type
        selected_wedding_package_id = None
        order_total_price = 0.0

        if form.service_type.data == "wedding":
            if form.wedding_package.data:
                selected_package = form.wedding_package.data
                selected_wedding_package_id = selected_package.id
                order_total_price = selected_package.price
            else:
                flash("Please select a wedding package.", "danger")
                return render_template(
                    "order.html", form=form, wedding_packages=wedding_packages
                )
        else:
            if form.total_price.data is None:
                flash("Please enter a total price for this service type.", "danger")
                return render_template(
                    "order.html", form=form, wedding_packages=wedding_packages
                )
            order_total_price = form.total_price.data

        order = Order(
            client_id=current_user.id,
            service_type=form.service_type.data,
            event_date=form.event_date.data,
            event_start_time=full_start_datetime,
            event_end_time=full_end_datetime,
            location=form.location.data,
            latitude=form.latitude.data if form.latitude.data else None,
            longitude=form.longitude.data if form.longitude.data else None,
            details=form.details.data,
            total_price=order_total_price,
            wedding_package_id=selected_wedding_package_id,  # Assign selected
            # package ID
            status="waiting_dp",
        )  # Set initial status to waiting_dp
        db.session.add(order)
        db.session.commit()

        # Create a CalendarEvent for this order and mark it unavailable
        calendar_event = CalendarEvent(
            title=f"Booking for {current_user.username}",
            start_time=full_start_datetime,
            end_time=full_end_datetime,
            description=f"Service: {form.service_type.data}",
            is_available=False,
            order_id=order.id,
        )
        db.session.add(calendar_event)
        db.session.commit()

        flash(
            "Your order has been placed successfully! Please proceed to DP payment.",
            "success",
        )
        return redirect(
            url_for("client.dp_payment", order_id=order.id)
        )  # Redirect to DP payment page
    return render_template("order.html", form=form, wedding_packages=wedding_packages)


@main.route("/api/unavailable_dates")
def unavailable_dates():
    # Fetch dates that are already booked or marked as unavailable
    booked_events = CalendarEvent.query.filter(
        or_(not CalendarEvent.is_available, CalendarEvent.order_id.isnot(None))
    ).all()

    unavailable_dates_list = []
    for event in booked_events:
        # Assuming single-day bookings for simplicity in date picker
        unavailable_dates_list.append(event.start_time.strftime("%Y-%m-%d"))

    return jsonify(unavailable_dates_list)
