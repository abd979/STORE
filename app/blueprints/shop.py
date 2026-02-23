from flask import Blueprint, render_template, request, abort, jsonify
from flask_login import login_required, current_user
from app.models import Product, Category, Review, db, Wishlist

shop_bp = Blueprint('shop', __name__)

@shop_bp.route('/')
def products():
    page = request.args.get('page', 1, type=int)
    category_slug = request.args.get('category', '')
    sort = request.args.get('sort', 'newest')
    search = request.args.get('q', '').strip()

    query = Product.query.filter_by(is_active=True)
    categories = Category.query.filter_by(is_active=True).order_by(Category.display_order).all()
    active_category = None

    if category_slug:
        cat = Category.query.filter_by(slug=category_slug, is_active=True).first()
        if cat:
            query = query.filter_by(category_id=cat.id)
            active_category = cat

    if search:
        query = query.filter(
            (Product.name.ilike(f'%{search}%')) |
            (Product.subtitle.ilike(f'%{search}%')) |
            (Product.description.ilike(f'%{search}%'))
        )

    if sort == 'price_asc':
        query = query.order_by(Product.price.asc())
    elif sort == 'price_desc':
        query = query.order_by(Product.price.desc())
    elif sort == 'name':
        query = query.order_by(Product.name.asc())
    else:
        query = query.order_by(Product.created_at.desc())

    pagination = query.paginate(page=page, per_page=12, error_out=False)
    return render_template('shop/products.html',
                           products=pagination.items,
                           pagination=pagination,
                           categories=categories,
                           active_category=active_category,
                           sort=sort,
                           search=search)

@shop_bp.route('/product/<slug>')
def product_detail(slug):
    product = Product.query.filter_by(slug=slug, is_active=True).first_or_404()
    reviews = Review.query.filter_by(product_id=product.id, is_approved=True).order_by(Review.created_at.desc()).all()
    related = Product.query.filter_by(category_id=product.category_id, is_active=True)\
                     .filter(Product.id != product.id).limit(4).all()
    in_wishlist = False
    if current_user.is_authenticated:
        in_wishlist = Wishlist.query.filter_by(user_id=current_user.id, product_id=product.id).first() is not None
    return render_template('shop/product_detail.html',
                           product=product, reviews=reviews,
                           related=related, in_wishlist=in_wishlist)

@shop_bp.route('/review/<int:product_id>', methods=['POST'])
@login_required
def add_review(product_id):
    product = Product.query.get_or_404(product_id)
    rating = request.form.get('rating', type=int)
    title = request.form.get('title', '').strip()
    body = request.form.get('body', '').strip()
    if not rating or not (1 <= rating <= 5):
        return jsonify({'error': 'Invalid rating'}), 400
    existing = Review.query.filter_by(product_id=product_id, user_id=current_user.id).first()
    if existing:
        existing.rating = rating
        existing.title = title
        existing.body = body
    else:
        r = Review(product_id=product_id, user_id=current_user.id,
                   rating=rating, title=title, body=body)
        db.session.add(r)
    db.session.commit()
    return jsonify({'success': True, 'average': product.average_rating, 'count': product.review_count})

@shop_bp.route('/wishlist/toggle/<int:product_id>', methods=['POST'])
@login_required
def toggle_wishlist(product_id):
    Product.query.get_or_404(product_id)
    existing = Wishlist.query.filter_by(user_id=current_user.id, product_id=product_id).first()
    if existing:
        db.session.delete(existing)
        db.session.commit()
        return jsonify({'in_wishlist': False})
    w = Wishlist(user_id=current_user.id, product_id=product_id)
    db.session.add(w)
    db.session.commit()
    return jsonify({'in_wishlist': True})
