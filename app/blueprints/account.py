from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.models import Order, Wishlist, Product, db, User

account_bp = Blueprint('account', __name__)

@account_bp.route('/')
@login_required
def dashboard():
    recent_orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).limit(5).all()
    order_count = Order.query.filter_by(user_id=current_user.id).count()
    wishlist_count = Wishlist.query.filter_by(user_id=current_user.id).count()
    pending_count = Order.query.filter_by(user_id=current_user.id, status='pending').count()
    return render_template('account/dashboard.html',
                           recent_orders=recent_orders, order_count=order_count,
                           wishlist_count=wishlist_count, pending_count=pending_count)

@account_bp.route('/orders')
@login_required
def orders():
    all_orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
    return render_template('account/orders.html', orders=all_orders)

@account_bp.route('/orders/<order_number>')
@login_required
def order_detail(order_number):
    order = Order.query.filter_by(order_number=order_number, user_id=current_user.id).first_or_404()
    return render_template('account/order_detail.html', order=order)

@account_bp.route('/wishlist')
@login_required
def wishlist():
    items = Wishlist.query.filter_by(user_id=current_user.id).all()
    return render_template('account/wishlist.html', items=items)

@account_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        current_user.first_name = request.form.get('first_name', '').strip()
        current_user.last_name = request.form.get('last_name', '').strip()
        current_user.phone = request.form.get('phone', '').strip()
        current_user.address_line1 = request.form.get('address_line1', '').strip()
        current_user.address_line2 = request.form.get('address_line2', '').strip()
        current_user.city = request.form.get('city', '').strip()
        current_user.postcode = request.form.get('postcode', '').strip()
        current_user.country = request.form.get('country', 'United Kingdom').strip()
        db.session.commit()
        flash('Profile updated successfully!', 'success')
    return render_template('account/profile.html')

@account_bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    current_pw = request.form.get('current_password', '')
    new_pw = request.form.get('new_password', '')
    confirm_pw = request.form.get('confirm_password', '')
    if not current_user.check_password(current_pw):
        flash('Current password is incorrect.', 'danger')
    elif new_pw != confirm_pw:
        flash('New passwords do not match.', 'danger')
    elif len(new_pw) < 6:
        flash('New password must be at least 6 characters.', 'danger')
    else:
        current_user.set_password(new_pw)
        db.session.commit()
        flash('Password changed successfully!', 'success')
    return redirect(url_for('account.profile'))

@account_bp.route('/orders/<order_number>/cancel', methods=['POST'])
@login_required
def cancel_order(order_number):
    order = Order.query.filter_by(order_number=order_number, user_id=current_user.id).first_or_404()
    
    # Check if order is cancellable (pending or confirmed)
    if order.status not in ['pending', 'confirmed']:
        flash(f'Order {order_number} cannot be cancelled as it is already {order.status}.', 'warning')
        return redirect(url_for('account.order_detail', order_number=order_number))
    
    order.status = 'cancelled'
    db.session.commit()
    
    flash(f'Order {order_number} has been cancelled successfully.', 'success')
    return redirect(url_for('account.orders'))
