from datetime import datetime
from app import db, login_manager, bcrypt
from flask_login import UserMixin


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    phone = db.Column(db.String(30))
    address_line1 = db.Column(db.String(200))
    address_line2 = db.Column(db.String(200))
    city = db.Column(db.String(100))
    postcode = db.Column(db.String(20))
    country = db.Column(db.String(100), default='United Kingdom')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    orders = db.relationship('Order', backref='customer', lazy=True)
    reviews = db.relationship('Review', backref='author', lazy=True)
    wishlist_items = db.relationship('Wishlist', backref='user', lazy=True)
    cart_items = db.relationship('CartItem', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name or ""}'.strip()

    def __repr__(self):
        return f'<User {self.email}>'


class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(120), unique=True, nullable=False)
    description = db.Column(db.Text)
    icon_svg = db.Column(db.Text)          # SVG markup for category icon
    display_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    products = db.relationship('Product', backref='category', lazy=True)

    @property
    def product_count(self):
        return Product.query.filter_by(category_id=self.id, is_active=True).count()

    def __repr__(self):
        return f'<Category {self.name}>'


class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(220), unique=True, nullable=False)
    subtitle = db.Column(db.String(200))       # e.g. "18K Rose Gold · Pink Diamond"
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    original_price = db.Column(db.Float)       # For sale items
    stock = db.Column(db.Integer, default=0)
    sku = db.Column(db.String(80))
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    image_filename = db.Column(db.String(200))  # main image
    image_filenames = db.Column(db.Text)        # JSON list of additional images or comma-separated
    badge = db.Column(db.String(50))            # "Bestseller", "New", "Limited", "Sale"
    badge_color = db.Column(db.String(20), default='black')  # 'black' or 'rose'
    material = db.Column(db.String(200))
    gemstone = db.Column(db.String(200))
    weight = db.Column(db.String(50))
    dimensions = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True)
    is_featured = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    gallery_images = db.relationship('ProductImage', backref='product', lazy=True, cascade='all, delete-orphan')
    reviews = db.relationship('Review', backref='product', lazy=True)
    cart_items = db.relationship('CartItem', backref='product', lazy=True)
    order_items = db.relationship('OrderItem', backref='product', lazy=True)
    wishlist_entries = db.relationship('Wishlist', backref='product', lazy=True)

    @property
    def all_images(self):
        images = [self.image_filename] if self.image_filename else []
        for img in self.gallery_images:
            images.append(img.filename)
        return images
    @property
    def average_rating(self):
        if not self.reviews:
            return 0
        return round(sum(r.rating for r in self.reviews) / len(self.reviews), 1)

    @property
    def review_count(self):
        return len(self.reviews)

    @property
    def is_on_sale(self):
        return self.original_price is not None and self.original_price > self.price

    @property
    def discount_percent(self):
        if self.is_on_sale:
            return int((1 - self.price / self.original_price) * 100)
        return 0

    @property
    def star_display(self):
        full = int(self.average_rating)
        half = 1 if self.average_rating - full >= 0.5 else 0
        empty = 5 - full - half
        return '★' * full + '☆' * half + '☆' * empty

    def __repr__(self):
        return f'<Product {self.name}>'


class CartItem(db.Model):
    __tablename__ = 'cart_items'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def subtotal(self):
        return self.product.price * self.quantity


class Wishlist(db.Model):
    __tablename__ = 'wishlist'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)


class Discount(db.Model):
    __tablename__ = 'discounts'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(200))
    discount_type = db.Column(db.String(20), default='percent')  # 'percent' or 'fixed'
    value = db.Column(db.Float, nullable=False)              # e.g. 10 for 10% or Rs10 off
    min_order_amount = db.Column(db.Float, default=0)
    max_uses = db.Column(db.Integer)                         # None = unlimited
    used_count = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    expires_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def is_valid(self, order_total):
        if not self.is_active:
            return False, 'This discount code is inactive.'
        if self.expires_at and datetime.utcnow() > self.expires_at:
            return False, 'This discount code has expired.'
        if self.max_uses and self.used_count >= self.max_uses:
            return False, 'This discount code has reached its usage limit.'
        if order_total < self.min_order_amount:
            return False, f'Minimum order of Rs{self.min_order_amount:.0f} required.'
        return True, ''

    def apply(self, order_total):
        if self.discount_type in ['percent', 'percentage']:
            return round(order_total * self.value / 100, 2)
        return min(self.value, order_total)

    def __repr__(self):
        return f'<Discount {self.code}>'


class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(20), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(30), default='pending')  # pending/confirmed/shipped/delivered/cancelled
    subtotal = db.Column(db.Float, nullable=False)
    shipping_cost = db.Column(db.Float, default=0)
    discount_amount = db.Column(db.Float, default=0)
    total = db.Column(db.Float, nullable=False)
    discount_code = db.Column(db.String(50))
    # Shipping address snapshot
    shipping_name = db.Column(db.String(160))
    shipping_email = db.Column(db.String(120))
    shipping_phone = db.Column(db.String(30))
    shipping_address1 = db.Column(db.String(200))
    shipping_address2 = db.Column(db.String(200))
    shipping_city = db.Column(db.String(100))
    shipping_postcode = db.Column(db.String(20))
    shipping_country = db.Column(db.String(100))
    # Payment
    payment_method = db.Column(db.String(50), default='card')
    payment_status = db.Column(db.String(30), default='pending')
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    items = db.relationship('OrderItem', backref='order', lazy=True)

    @property
    def status_badge_class(self):
        return {
            'pending': 'badge-warning',
            'confirmed': 'badge-info',
            'shipped': 'badge-primary',
            'delivered': 'badge-success',
            'cancelled': 'badge-danger',
        }.get(self.status, 'badge-secondary')

    def __repr__(self):
        return f'<Order {self.order_number}>'


class OrderItem(db.Model):
    __tablename__ = 'order_items'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)   # price at time of order
    subtotal = db.Column(db.Float, nullable=False)


class Review(db.Model):
    __tablename__ = 'reviews'
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1-5
    title = db.Column(db.String(200))
    body = db.Column(db.Text)
    is_verified = db.Column(db.Boolean, default=False)
    is_approved = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Review {self.id} Product {self.product_id}>'


class Newsletter(db.Model):
    __tablename__ = 'newsletter'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)


class SiteSettings(db.Model):
    __tablename__ = 'site_settings'
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text)
    label = db.Column(db.String(200))

    @staticmethod
    def get(key, default=None):
        s = SiteSettings.query.filter_by(key=key).first()
        return s.value if s else default

    @staticmethod
    def set(key, value):
        s = SiteSettings.query.filter_by(key=key).first()
        if s:
            s.value = value
        else:
            s = SiteSettings(key=key, value=value)
            db.session.add(s)
        db.session.commit()


class NavigationItem(db.Model):
    __tablename__ = 'navigation_items'
    id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.String(100), nullable=False)
    url = db.Column(db.String(2048), nullable=False)  # Can be url_for name or external
    display_order = db.Column(db.Integer, default=0)
    is_external = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<NavigationItem {self.label}>'


class ProductImage(db.Model):
    __tablename__ = 'product_images'
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    filename = db.Column(db.String(200), nullable=False)
    display_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<ProductImage {self.filename}>'
