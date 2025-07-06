from flask import render_template, Blueprint, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from models import Order, Testimonial, db, User
from forms import TestimonialSubmissionForm, TestimonialEditForm, UserEditForm, DPPaymentForm
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from . import client

@client.app_template_global('get_testimonial_for_order')
def get_testimonial_for_order(order_id):
    return Testimonial.query.filter_by(order_id=order_id, user_id=current_user.id).first()

@client.route('/dashboard')
@login_required
def dashboard():
    orders = Order.query.filter_by(client_id=current_user.id).all()
    return render_template('client/dashboard.html', orders=orders)

@client.route('/submit_testimonial/<int:order_id>', methods=['GET', 'POST'])
@login_required
def submit_testimonial(order_id):
    order = Order.query.get_or_404(order_id)

    # Ensure the order belongs to the current user
    if order.client_id != current_user.id:
        flash('You do not have permission to submit a testimonial for this order.', 'danger')
        return redirect(url_for('client.dashboard'))

    # Ensure the order is completed and allows testimonial submission
    if order.status != 'completed' or not order.can_submit_testimonial:
        flash('This order is not yet completed or does not allow testimonial submission.', 'danger')
        return redirect(url_for('client.dashboard'))

    # Ensure client hasn't already submitted a testimonial for this order
    existing_testimonial = Testimonial.query.filter_by(order_id=order_id, user_id=current_user.id).first()
    if existing_testimonial:
        flash('You have already submitted a testimonial for this order.', 'warning')
        return redirect(url_for('client.dashboard'))

    form = TestimonialSubmissionForm()
    if form.validate_on_submit():
        testimonial = Testimonial(
            client_name=current_user.full_name, # Use client's full name
            testimonial_text=form.testimonial_text.data,
            rating=form.rating.data,
            user_id=current_user.id,
            order_id=order.id,
            is_approved=False # Admin needs to approve
        )
        db.session.add(testimonial)
        db.session.commit()
        flash('Your testimonial has been submitted for review!', 'success')
        return redirect(url_for('client.dashboard'))

    return render_template('client/submit_testimonial.html', form=form, order=order)

@client.route('/edit_testimonial/<int:testimonial_id>', methods=['GET', 'POST'])
@login_required
def edit_testimonial_client(testimonial_id):
    testimonial = Testimonial.query.get_or_404(testimonial_id)

    # Ensure the testimonial belongs to the current user
    if testimonial.user_id != current_user.id:
        flash('You do not have permission to edit this testimonial.', 'danger')
        return redirect(url_for('client.dashboard'))

    # Prevent editing if already approved by admin
    if testimonial.is_approved:
        flash('This testimonial has already been approved and cannot be edited.', 'warning')
        return redirect(url_for('client.dashboard'))

    form = TestimonialEditForm()
    if form.validate_on_submit():
        testimonial.testimonial_text = form.testimonial_text.data
        testimonial.rating = form.rating.data
        db.session.commit()
        flash('Your testimonial has been updated!', 'success')
        return redirect(url_for('client.dashboard'))
    elif request.method == 'GET':
        form.testimonial_text.data = testimonial.testimonial_text
        form.rating.data = testimonial.rating

    return render_template('client/edit_testimonial.html', form=form, testimonial=testimonial)

@client.route('/delete_testimonial/<int:testimonial_id>', methods=['POST'])
@login_required
def delete_testimonial_client(testimonial_id):
    testimonial = Testimonial.query.get_or_404(testimonial_id)

    # Ensure the testimonial belongs to the current user
    if testimonial.user_id != current_user.id:
        flash('You do not have permission to delete this testimonial.', 'danger')
        return redirect(url_for('client.dashboard'))

    # Prevent deletion if already approved by admin
    if testimonial.is_approved:
        flash('This testimonial has already been approved and cannot be deleted.', 'warning')
        return redirect(url_for('client.dashboard'))

    db.session.delete(testimonial)
    db.session.commit()
    flash('Your testimonial has been deleted!', 'success')
    return redirect(url_for('client.dashboard'))

@client.route('/delete_order/<int:order_id>', methods=['POST'])
@login_required
def delete_order(order_id):
    order = Order.query.get_or_404(order_id)

    # Ensure the order belongs to the current user
    if order.client_id != current_user.id:
        flash('You do not have permission to delete this order.', 'danger')
        return redirect(url_for('client.dashboard'))

    # Only allow deletion if the order is rejected
    if order.status != 'rejected':
        flash('Only rejected orders can be deleted.', 'danger')
        return redirect(url_for('client.dashboard'))

    # Delete associated CalendarEvent if exists
    if order.calendar_event:
        db.session.delete(order.calendar_event)
    
    # Delete associated Testimonial if exists
    testimonial = Testimonial.query.filter_by(order_id=order.id).first()
    if testimonial:
        db.session.delete(testimonial)

    db.session.delete(order)
    db.session.commit()
    flash('Order has been deleted successfully!', 'success')
    return redirect(url_for('client.dashboard'))

@client.route('/dp_payment/<int:order_id>', methods=['GET', 'POST'])
@login_required
def dp_payment(order_id):
    order = Order.query.get_or_404(order_id)
    form = DPPaymentForm()
    if order.client_id != current_user.id:
        flash('You do not have permission to view this page.', 'danger')
        return redirect(url_for('client.dashboard'))
    if order.status != 'waiting_dp':
        flash('This order is not awaiting DP payment.', 'warning')
        return redirect(url_for('client.dashboard'))
    
    dp_amount = order.total_price * 0.15 # Calculate 15% DP
    return render_template('client/dp_payment.html', order=order, dp_amount=dp_amount, form=form)

@client.route('/pay_dp/<int:order_id>', methods=['POST'])
@login_required
def pay_dp(order_id):
    order = Order.query.get_or_404(order_id)
    form = DPPaymentForm()

    if order.client_id != current_user.id:
        flash('You do not have permission to perform this action.', 'danger')
        return redirect(url_for('client.dashboard'))

    if order.status != 'waiting_dp':
        flash('This order is not awaiting DP payment.', 'warning')
        return redirect(url_for('client.dashboard'))

    # Check if more than 1 hour has passed since order creation
    time_elapsed = datetime.utcnow() - order.created_at
    if time_elapsed > timedelta(hours=1):
        order.status = 'cancelled'  # Or 'timed_out'
        db.session.commit()
        flash('Your order has been automatically cancelled because the DP payment was not received within 1 hour. Please place a new order if you wish to proceed.', 'danger')
        return redirect(url_for('client.dashboard'))

    if form.validate_on_submit():
        if form.payment_proof.data:
            # Save the uploaded file
            filename = secure_filename(form.payment_proof.data.filename)
            upload_folder = os.path.join(current_app.root_path, 'static', 'payment_proofs')
            os.makedirs(upload_folder, exist_ok=True) # Ensure the directory exists
            file_path = os.path.join(upload_folder, filename)
            form.payment_proof.data.save(file_path)
            order.dp_payment_proof = filename # Store only the filename

        order.dp_paid = order.total_price * 0.15 # Calculate 15% DP
        order.status = 'waiting_approval'
        db.session.commit()
        flash('DP payment proof submitted successfully! Your order is now awaiting admin approval.', 'success')
        return redirect(url_for('client.dashboard'))
    else:
        # If form validation fails, re-render the dp_payment page with errors
        dp_amount = order.total_price * 0.15
        return render_template('client/dp_payment.html', order=order, dp_amount=dp_amount, form=form)

@client.route('/profile', methods=['GET', 'POST'])
@login_required
def edit_profile_client():
    form = UserEditForm(original_username=current_user.username, original_email=current_user.email)
    if form.validate_on_submit():
        current_user.full_name = form.full_name.data
        current_user.username = form.username.data
        current_user.email = form.email.data
        current_user.whatsapp_number = form.whatsapp_number.data
        if form.password.data:
            current_user.password = generate_password_hash(form.password.data, method='pbkdf2:sha256')
        db.session.commit()
        flash('Your profile has been updated successfully!', 'success')
        return redirect(url_for('client.dashboard'))
    elif request.method == 'GET':
        form.full_name.data = current_user.full_name
        form.username.data = current_user.username
        form.email.data = current_user.email
        form.whatsapp_number.data = current_user.whatsapp_number
    return render_template('edit_profile.html', form=form, user=current_user, title='Edit Client Profile')
