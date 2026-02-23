from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from functools import wraps
from app.models import (Product, Category, Order, User, Discount, Review,
                        Newsletter, SiteSettings, NavigationItem, ProductImage, db)
from slugify import slugify
import os, uuid
from config import Config

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Admin access required.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated

# ── DASHBOARD ───────────────────────────────────────────────────────────────
@admin_bp.route('/')
@login_required
@admin_required
def dashboard():
    stats = {
        'products': Product.query.filter_by(is_active=True).count(),
        'categories': Category.query.filter_by(is_active=True).count(),
        'orders': Order.query.count(),
        'users': User.query.filter_by(is_admin=False).count(),
        'revenue': db.session.query(db.func.sum(Order.total)).filter(
            Order.payment_status == 'paid').scalar() or 0,
        'pending_orders': Order.query.filter_by(status='pending').count(),
    }
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(8).all()
    recent_products = Product.query.order_by(Product.created_at.desc()).limit(5).all()
    return render_template('admin/dashboard.html', stats=stats,
                           recent_orders=recent_orders, recent_products=recent_products)

# ── PRODUCTS ─────────────────────────────────────────────────────────────────
@admin_bp.route('/products')
@login_required
@admin_required
def products():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('q', '')
    query = Product.query
    if search:
        query = query.filter(Product.name.ilike(f'%{search}%'))
    products = query.order_by(Product.created_at.desc()).paginate(page=page, per_page=20, error_out=False)
    return render_template('admin/products.html', products=products, search=search)

@admin_bp.route('/products/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_product():
    categories = Category.query.filter_by(is_active=True).all()
    if request.method == 'POST':
        f = request.form
        name = f.get('name', '').strip()
        if not name:
            flash('Product name is required.', 'danger')
            return render_template('admin/product_form.html', categories=categories, product=None)

        slug = slugify(name)
        # Ensure unique slug
        base_slug = slug
        counter = 1
        while Product.query.filter_by(slug=slug).first():
            slug = f'{base_slug}-{counter}'
            counter += 1

        orig_price = f.get('original_price', '').strip()
        p = Product(
            name=name, slug=slug,
            subtitle=f.get('subtitle', ''),
            description=f.get('description', ''),
            price=float(f.get('price', 0)),
            original_price=float(orig_price) if orig_price else None,
            stock=int(f.get('stock', 0)),
            sku=f.get('sku', ''),
            category_id=int(f.get('category_id')),
            badge=f.get('badge', ''),
            badge_color=f.get('badge_color', 'black'),
            material=f.get('material', ''),
            gemstone=f.get('gemstone', ''),
            weight=f.get('weight', ''),
            dimensions=f.get('dimensions', ''),
            is_active=f.get('is_active') == 'on',
            is_featured=f.get('is_featured') == 'on',
        )
        # Handle images
        image = request.files.get('image')
        if image and image.filename:
            filename = f'{uuid.uuid4().hex}_{image.filename}'
            image.save(os.path.join(Config.UPLOAD_FOLDER, filename))
            p.image_filename = filename

        # Additional gallery images
        gallery_files = request.files.getlist('gallery_images')
        for file in gallery_files:
            if file and file.filename:
                fname = f'{uuid.uuid4().hex}_{file.filename}'
                file.save(os.path.join(Config.UPLOAD_FOLDER, fname))
                img = ProductImage(product=p, filename=fname)
                db.session.add(img)

        db.session.add(p)
        db.session.commit()
        flash(f'Product "{name}" created!', 'success')
        return redirect(url_for('admin.products'))

    return render_template('admin/product_form.html', categories=categories, product=None)

@admin_bp.route('/products/<int:pid>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_product(pid):
    p = Product.query.get_or_404(pid)
    categories = Category.query.filter_by(is_active=True).all()
    if request.method == 'POST':
        f = request.form
        p.name = f.get('name', '').strip()
        p.subtitle = f.get('subtitle', '')
        p.description = f.get('description', '')
        p.price = float(f.get('price', 0))
        orig_price = f.get('original_price', '').strip()
        p.original_price = float(orig_price) if orig_price else None
        p.stock = int(f.get('stock', 0))
        p.sku = f.get('sku', '')
        p.category_id = int(f.get('category_id'))
        p.card_bg_css = f.get('card_bg_css', '')
        p.badge = f.get('badge', '')
        p.badge_color = f.get('badge_color', 'black')
        p.material = f.get('material', '')
        p.gemstone = f.get('gemstone', '')
        p.weight = f.get('weight', '')
        p.dimensions = f.get('dimensions', '')
        p.is_active = f.get('is_active') == 'on'
        p.is_featured = f.get('is_featured') == 'on'

        image = request.files.get('image')
        if image and image.filename:
            filename = f'{uuid.uuid4().hex}_{image.filename}'
            image.save(os.path.join(Config.UPLOAD_FOLDER, filename))
            p.image_filename = filename

        # Additional gallery images
        gallery_files = request.files.getlist('gallery_images')
        for file in gallery_files:
            if file and file.filename:
                fname = f'{uuid.uuid4().hex}_{file.filename}'
                file.save(os.path.join(Config.UPLOAD_FOLDER, fname))
                img = ProductImage(product=p, filename=fname)
                db.session.add(img)

        # Handle image deletion if requested
        delete_image_ids = f.getlist('delete_image_ids')
        for img_id in delete_image_ids:
            img = ProductImage.query.get(int(img_id))
            if img and img.product_id == p.id:
                # Optionally delete file from disk here
                db.session.delete(img)

        db.session.commit()
        flash(f'Product "{p.name}" updated!', 'success')
        return redirect(url_for('admin.products'))

    return render_template('admin/product_form.html', categories=categories, product=p)

@admin_bp.route('/products/<int:pid>/delete', methods=['POST'])
@login_required
@admin_required
def delete_product(pid):
    p = Product.query.get_or_404(pid)
    p.is_active = False
    db.session.commit()
    return jsonify({'success': True})

# ── CATEGORIES ───────────────────────────────────────────────────────────────
@admin_bp.route('/categories')
@login_required
@admin_required
def categories():
    cats = Category.query.order_by(Category.display_order).all()
    return render_template('admin/categories.html', categories=cats)

@admin_bp.route('/categories/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_category():
    if request.method == 'POST':
        f = request.form
        name = f.get('name', '').strip()
        slug = slugify(name)
        base_slug = slug
        counter = 1
        while Category.query.filter_by(slug=slug).first():
            slug = f'{base_slug}-{counter}'
            counter += 1
        cat = Category(
            name=name, slug=slug,
            description=f.get('description', ''),
            icon_svg=f.get('icon_svg', ''),
            display_order=int(f.get('display_order', 0)),
            is_active=f.get('is_active') == 'on'
        )
        db.session.add(cat)
        db.session.commit()
        flash(f'Category "{name}" created!', 'success')
        return redirect(url_for('admin.categories'))
    return render_template('admin/category_form.html', category=None)

@admin_bp.route('/categories/<int:cid>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_category(cid):
    cat = Category.query.get_or_404(cid)
    if request.method == 'POST':
        f = request.form
        cat.name = f.get('name', '').strip()
        cat.description = f.get('description', '')
        cat.icon_svg = f.get('icon_svg', '')
        cat.display_order = int(f.get('display_order', 0))
        cat.is_active = f.get('is_active') == 'on'
        db.session.commit()
        flash(f'Category updated!', 'success')
        return redirect(url_for('admin.categories'))
    return render_template('admin/category_form.html', category=cat)

@admin_bp.route('/categories/<int:cid>/delete', methods=['POST'])
@login_required
@admin_required
def delete_category(cid):
    cat = Category.query.get_or_404(cid)
    cat.is_active = False
    db.session.commit()
    return jsonify({'success': True})

# ── ORDERS ────────────────────────────────────────────────────────────────────
@admin_bp.route('/orders')
@login_required
@admin_required
def orders():
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '')
    query = Order.query
    if status:
        query = query.filter_by(status=status)
    orders = query.order_by(Order.created_at.desc()).paginate(page=page, per_page=20, error_out=False)
    return render_template('admin/orders.html', orders=orders, status=status)

@admin_bp.route('/orders/<int:oid>')
@login_required
@admin_required
def order_detail(oid):
    order = Order.query.get_or_404(oid)
    return render_template('admin/order_detail.html', order=order)

@admin_bp.route('/orders/<int:oid>/status', methods=['POST'])
@login_required
@admin_required
def update_order_status(oid):
    order = Order.query.get_or_404(oid)
    order.status = request.form.get('status', order.status)
    order.payment_status = request.form.get('payment_status', order.payment_status)
    db.session.commit()
    flash(f'Order {order.order_number} updated.', 'success')
    return redirect(url_for('admin.order_detail', oid=oid))

# ── DISCOUNTS ─────────────────────────────────────────────────────────────────
@admin_bp.route('/discounts')
@login_required
@admin_required
def discounts():
    all_discounts = Discount.query.order_by(Discount.created_at.desc()).all()
    return render_template('admin/discounts.html', discounts=all_discounts)

@admin_bp.route('/discounts/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_discount():
    if request.method == 'POST':
        f = request.form
        expires_raw = f.get('expires_at', '').strip()
        from datetime import datetime
        expires = datetime.strptime(expires_raw, '%Y-%m-%d') if expires_raw else None
        max_uses_raw = f.get('max_uses', '').strip()
        d = Discount(
            code=f.get('code', '').strip().upper(),
            description=f.get('description', ''),
            discount_type=f.get('discount_type', 'percent'),
            value=float(f.get('value', 0)),
            min_order_amount=float(f.get('min_order_amount', 0)),
            max_uses=int(max_uses_raw) if max_uses_raw else None,
            is_active=f.get('is_active') == 'on',
            expires_at=expires
        )
        db.session.add(d)
        db.session.commit()
        flash(f'Discount code "{d.code}" created!', 'success')
        return redirect(url_for('admin.discounts'))
    return render_template('admin/discount_form.html', discount=None)

@admin_bp.route('/discounts/<int:did>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_discount(did):
    d = Discount.query.get_or_404(did)
    if request.method == 'POST':
        f = request.form
        expires_raw = f.get('expires_at', '').strip()
        from datetime import datetime
        d.code = f.get('code', '').strip().upper()
        d.description = f.get('description', '')
        d.discount_type = f.get('discount_type', 'percent')
        d.value = float(f.get('value', 0))
        d.min_order_amount = float(f.get('min_order_amount', 0))
        max_uses_raw = f.get('max_uses', '').strip()
        d.max_uses = int(max_uses_raw) if max_uses_raw else None
        d.is_active = f.get('is_active') == 'on'
        d.expires_at = datetime.strptime(expires_raw, '%Y-%m-%d') if expires_raw else None
        db.session.commit()
        flash('Discount updated!', 'success')
        return redirect(url_for('admin.discounts'))
    return render_template('admin/discount_form.html', discount=d)

@admin_bp.route('/discounts/<int:did>/delete', methods=['POST'])
@login_required
@admin_required
def delete_discount(did):
    d = Discount.query.get_or_404(did)
    db.session.delete(d)
    db.session.commit()
    return jsonify({'success': True})

# ── USERS ─────────────────────────────────────────────────────────────────────
@admin_bp.route('/users')
@login_required
@admin_required
def users():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('q', '')
    query = User.query
    if search:
        query = query.filter(
            (User.email.ilike(f'%{search}%')) |
            (User.first_name.ilike(f'%{search}%')) |
            (User.last_name.ilike(f'%{search}%'))
        )
    users = query.order_by(User.created_at.desc()).paginate(page=page, per_page=20, error_out=False)
    return render_template('admin/users.html', users=users, search=search)

@admin_bp.route('/users/<int:uid>/toggle-admin', methods=['POST'])
@login_required
@admin_required
def toggle_admin(uid):
    user = User.query.get_or_404(uid)
    if user.id == current_user.id:
        return jsonify({'error': 'Cannot change your own admin status'}), 400
    user.is_admin = not user.is_admin
    db.session.commit()
    return jsonify({'success': True, 'is_admin': user.is_admin})

@admin_bp.route('/users/<int:uid>/toggle-active', methods=['POST'])
@login_required
@admin_required
def toggle_user_active(uid):
    user = User.query.get_or_404(uid)
    if user.id == current_user.id:
        return jsonify({'error': 'Cannot deactivate yourself'}), 400
    user.is_active = not user.is_active
    db.session.commit()
    return jsonify({'success': True, 'is_active': user.is_active})

# ── REVIEWS ───────────────────────────────────────────────────────────────────
@admin_bp.route('/reviews')
@login_required
@admin_required
def reviews():
    page = request.args.get('page', 1, type=int)
    all_reviews = Review.query.order_by(Review.created_at.desc()).paginate(page=page, per_page=20, error_out=False)
    return render_template('admin/reviews.html', reviews=all_reviews)

@admin_bp.route('/reviews/<int:rid>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_review(rid):
    r = Review.query.get_or_404(rid)
    r.is_approved = not r.is_approved
    db.session.commit()
    return jsonify({'success': True, 'approved': r.is_approved})

@admin_bp.route('/reviews/<int:rid>/delete', methods=['POST'])
@login_required
@admin_required
def delete_review(rid):
    r = Review.query.get_or_404(rid)
    db.session.delete(r)
    db.session.commit()
    return jsonify({'success': True})

# ── NEWSLETTER ────────────────────────────────────────────────────────────────
@admin_bp.route('/newsletter')
@login_required
@admin_required
def newsletter_list():
    page = request.args.get('page', 1, type=int)
    subs = Newsletter.query.filter_by(is_active=True).order_by(Newsletter.created_at.desc()).paginate(page=page, per_page=50, error_out=False)
    return render_template('admin/newsletter.html', subscribers=subs)

# ── SETTINGS ──────────────────────────────────────────────────────────────────
@admin_bp.route('/settings', methods=['GET', 'POST'])
@login_required
@admin_required
def settings():
    if request.method == 'POST':
        for key, value in request.form.items():
            if key != 'csrf_token':
                SiteSettings.set(key, value)
        flash('Settings saved!', 'success')

    all_settings = SiteSettings.query.all()
    settings_dict = {s.key: s.value for s in all_settings}
    return render_template('admin/settings.html', settings=settings_dict)
# ── NAVIGATION ───────────────────────────────────────────────────────────────
@admin_bp.route('/navigation')
@login_required
@admin_required
def navigation():
    items = NavigationItem.query.order_by(NavigationItem.display_order.asc()).all()
    return render_template('admin/navigation.html', items=items)

@admin_bp.route('/navigation/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_nav_item():
    if request.method == 'POST':
        item = NavigationItem(
            label=request.form.get('label'),
            url=request.form.get('url'),
            display_order=int(request.form.get('display_order', 0)),
            is_external=request.form.get('is_external') == 'on',
            is_active=request.form.get('is_active') == 'on'
        )
        db.session.add(item)
        db.session.commit()
        flash('Navigation item created.', 'success')
        return redirect(url_for('admin.navigation'))
    return render_template('admin/nav_item_form.html', item=None)

@admin_bp.route('/navigation/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_nav_item(id):
    item = NavigationItem.query.get_or_404(id)
    if request.method == 'POST':
        item.label = request.form.get('label')
        item.url = request.form.get('url')
        item.display_order = int(request.form.get('display_order', 0))
        item.is_external = request.form.get('is_external') == 'on'
        item.is_active = request.form.get('is_active') == 'on'
        db.session.commit()
        flash('Navigation item updated.', 'success')
        return redirect(url_for('admin.navigation'))
    return render_template('admin/nav_item_form.html', item=item)

@admin_bp.route('/navigation/delete/<int:id>', methods=['POST'])
@login_required
@admin_required
def delete_nav_item(id):
    item = NavigationItem.query.get_or_404(id)
    db.session.delete(item)
    db.session.commit()
    return jsonify({'success': True})
