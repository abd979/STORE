from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import login_required, current_user
from app.models import CartItem, Product, Order, OrderItem, Discount, SiteSettings, db
from app import db
import uuid
from datetime import datetime
from config import Config

cart_bp = Blueprint('cart', __name__)

def get_cart_items():
    return CartItem.query.filter_by(user_id=current_user.id).all()

def get_cart_total(items):
    return sum(i.subtotal for i in items)

def recalculate_discount(subtotal):
    discount_id = session.get('discount_id')
    if not discount_id:
        session.pop('discount_amount', None)
        session.pop('discount_code', None)
        return 0
    
    discount = Discount.query.get(discount_id)
    if not discount:
        session.pop('discount_id', None)
        session.pop('discount_amount', None)
        session.pop('discount_code', None)
        return 0
    
    valid, msg = discount.is_valid(subtotal)
    if not valid:
        # If no longer valid (e.g. subtotal < min_order), remove discount
        session.pop('discount_id', None)
        session.pop('discount_amount', None)
        session.pop('discount_code', None)
        return 0
    
    amount = discount.apply(subtotal)
    session['discount_amount'] = amount
    return amount

@cart_bp.route('/')
@login_required
def view_cart():
    items = get_cart_items()
    subtotal = get_cart_total(items)
    threshold = float(SiteSettings.get('free_shipping_threshold', 200))
    shipping_cost = float(SiteSettings.get('shipping_cost', 9.95))
    shipping = 0 if subtotal >= threshold else shipping_cost
    discount_amount = float(session.get('discount_amount', 0))
    discount_code = session.get('discount_code', '')
    total = max(0, subtotal + shipping - discount_amount)
    return render_template('shop/cart.html',
                           items=items, subtotal=subtotal,
                           shipping=shipping, discount_amount=discount_amount,
                           discount_code=discount_code, total=total,
                           threshold=threshold)

@cart_bp.route('/add/<int:product_id>', methods=['POST'])
@login_required
def add_to_cart(product_id):
    product = Product.query.get_or_404(product_id)
    qty = int(request.form.get('quantity', 1))
    existing = CartItem.query.filter_by(user_id=current_user.id, product_id=product_id).first()
    if existing:
        existing.quantity = min(existing.quantity + qty, product.stock)
    else:
        if product.stock < qty:
            return jsonify({'error': 'Insufficient stock'}), 400
        item = CartItem(user_id=current_user.id, product_id=product_id, quantity=qty)
        db.session.add(item)
    db.session.commit()
    cart_count = CartItem.query.filter_by(user_id=current_user.id).count()
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': True, 'cart_count': cart_count, 'message': f'{product.name} added to cart!'})
    flash(f'{product.name} added to your cart!', 'success')
    return redirect(url_for('cart.view_cart'))

@cart_bp.route('/update/<int:item_id>', methods=['POST'])
@login_required
def update_cart(item_id):
    item = CartItem.query.filter_by(id=item_id, user_id=current_user.id).first_or_404()
    qty = int(request.form.get('quantity', 1))
    if qty <= 0:
        db.session.delete(item)
    else:
        item.quantity = min(qty, item.product.stock)
    db.session.commit()
    items = get_cart_items()
    subtotal = get_cart_total(items)
    discount_amount = recalculate_discount(subtotal)
    threshold = float(SiteSettings.get('free_shipping_threshold', 200))
    shipping_cost = float(SiteSettings.get('shipping_cost', 9.95))
    shipping = 0 if subtotal >= threshold else shipping_cost
    total = max(0, subtotal + shipping - discount_amount)
    
    return jsonify({
        'success': True, 
        'subtotal': subtotal, 
        'shipping': shipping,
        'discount_amount': discount_amount,
        'discount_code': session.get('discount_code', ''),
        'total': total, 
        'cart_count': len(items),
        'item_subtotal': item.subtotal if qty > 0 else 0,
        'threshold': threshold,
        'actual_quantity': item.quantity if qty > 0 else 0,
        'stock_limit_reached': qty > item.product.stock
    })

@cart_bp.route('/remove/<int:item_id>', methods=['POST'])
@login_required
def remove_from_cart(item_id):
    item = CartItem.query.filter_by(id=item_id, user_id=current_user.id).first_or_404()
    db.session.delete(item)
    db.session.commit()
    items = get_cart_items()
    subtotal = get_cart_total(items)
    discount_amount = recalculate_discount(subtotal)
    threshold = float(SiteSettings.get('free_shipping_threshold', 200))
    shipping_cost = float(SiteSettings.get('shipping_cost', 9.95))
    shipping = 0 if subtotal >= threshold else shipping_cost
    total = max(0, subtotal + shipping - discount_amount)
    
    return jsonify({
        'success': True, 
        'subtotal': subtotal, 
        'shipping': shipping,
        'discount_amount': discount_amount,
        'discount_code': session.get('discount_code', ''),
        'total': total, 
        'cart_count': len(items)
    })

@cart_bp.route('/apply-coupon', methods=['POST'])
@login_required
def apply_coupon():
    code = request.form.get('code', '').strip().upper()
    items = get_cart_items()
    subtotal = get_cart_total(items)
    discount = Discount.query.filter_by(code=code).first()
    if not discount:
        return jsonify({'success': False, 'message': 'Invalid discount code.'})
    valid, msg = discount.is_valid(subtotal)
    if not valid:
        return jsonify({'success': False, 'message': msg})
    amount = discount.apply(subtotal)
    session['discount_code'] = code
    session['discount_amount'] = amount
    session['discount_id'] = discount.id
    threshold = float(SiteSettings.get('free_shipping_threshold', 200))
    shipping_cost = float(SiteSettings.get('shipping_cost', 9.95))
    shipping = 0 if subtotal >= threshold else shipping_cost
    total = max(0, subtotal + shipping - amount)
    return jsonify({'success': True, 'discount_amount': amount,
                    'total': total, 'message': f'Code "{code}" applied! You saved Rs{amount:.2f}'})

@cart_bp.route('/remove-coupon', methods=['POST'])
@login_required
def remove_coupon():
    session.pop('discount_code', None)
    session.pop('discount_amount', None)
    session.pop('discount_id', None)
    return jsonify({'success': True})

@cart_bp.route('/count')
@login_required
def cart_count():
    count = CartItem.query.filter_by(user_id=current_user.id).count()
    return jsonify({'count': count})

@cart_bp.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    items = get_cart_items()
    if not items:
        flash('Your cart is empty.', 'warning')
        return redirect(url_for('cart.view_cart'))
    subtotal = get_cart_total(items)
    threshold = float(SiteSettings.get('free_shipping_threshold', 200))
    shipping_cost = float(SiteSettings.get('shipping_cost', 9.95))
    shipping = 0 if subtotal >= threshold else shipping_cost
    discount_amount = float(session.get('discount_amount', 0))
    total = max(0, subtotal + shipping - discount_amount)

    if request.method == 'POST':
        # Build order
        order_number = 'ORD-' + uuid.uuid4().hex[:8].upper()
        order = Order(
            order_number=order_number,
            user_id=current_user.id,
            subtotal=subtotal,
            shipping_cost=shipping,
            discount_amount=discount_amount,
            total=total,
            discount_code=session.get('discount_code', ''),
            shipping_name=request.form.get('full_name'),
            shipping_email=request.form.get('email'),
            shipping_phone=request.form.get('phone'),
            shipping_address1=request.form.get('address1'),
            shipping_address2=request.form.get('address2', ''),
            shipping_city=request.form.get('city'),
            shipping_postcode=request.form.get('postcode'),
            shipping_country=request.form.get('country', 'United Kingdom'),
            payment_method=request.form.get('payment_method', 'card'),
            status='confirmed',
            payment_status='paid',
            notes=request.form.get('notes', '')
        )
        db.session.add(order)
        db.session.flush()

        for item in items:
            oi = OrderItem(
                order_id=order.id,
                product_id=item.product_id,
                quantity=item.quantity,
                unit_price=item.product.price,
                subtotal=item.subtotal
            )
            item.product.stock = max(0, item.product.stock - item.quantity)
            db.session.add(oi)
            db.session.delete(item)

        # Mark discount used
        discount_id = session.get('discount_id')
        if discount_id:
            d = Discount.query.get(discount_id)
            if d:
                d.used_count += 1

        db.session.commit()
        session.pop('discount_code', None)
        session.pop('discount_amount', None)
        session.pop('discount_id', None)
        return redirect(url_for('cart.order_confirmation', order_number=order_number))

    return render_template('shop/checkout.html',
                           items=items, subtotal=subtotal,
                           shipping=shipping, discount_amount=discount_amount,
                           total=total, user=current_user)

@cart_bp.route('/confirmation/<order_number>')
@login_required
def order_confirmation(order_number):
    order = Order.query.filter_by(order_number=order_number, user_id=current_user.id).first_or_404()
    return render_template('shop/order_confirmation.html', order=order)
