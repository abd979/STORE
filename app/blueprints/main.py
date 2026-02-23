from flask import Blueprint, render_template, redirect, url_for, request, jsonify
from app.models import Product, Category, Review, Newsletter, db
from sqlalchemy import func

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    featured = Product.query.filter_by(is_featured=True, is_active=True).limit(6).all()
    categories = Category.query.filter_by(is_active=True).order_by(Category.display_order).all()
    return render_template('main/index.html', featured=featured, categories=categories)

@main_bp.route('/newsletter', methods=['POST'])
def newsletter():
    email = request.form.get('email', '').strip()
    if email:
        existing = Newsletter.query.filter_by(email=email).first()
        if not existing:
            sub = Newsletter(email=email)
            db.session.add(sub)
            db.session.commit()
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': True})
    return redirect(url_for('main.index'))

@main_bp.route('/bespoke')
def bespoke():
    return render_template('main/bespoke.html')

@main_bp.route('/our-story')
def our_story():
    return render_template('main/our_story.html')
