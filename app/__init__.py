from flask import Flask, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_wtf import CSRFProtect
from config import Config

db = SQLAlchemy()
login_manager = LoginManager()
bcrypt = Bcrypt()
csrf = CSRFProtect()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)
    bcrypt.init_app(app)
    csrf.init_app(app)

    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'

    from app.blueprints.main import main_bp
    from app.blueprints.auth import auth_bp
    from app.blueprints.shop import shop_bp
    from app.blueprints.cart import cart_bp
    from app.blueprints.admin import admin_bp
    from app.blueprints.account import account_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(shop_bp, url_prefix='/shop')
    app.register_blueprint(cart_bp, url_prefix='/cart')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(account_bp, url_prefix='/account')
    @app.context_processor
    def inject_nav():
        from app.models import NavigationItem
        def resolve_url(url_val):
            # If it's a route name like 'shop.products'
            try:
                if '.' in url_val:
                    # check if it has a category suffix like shop.products?category=rings
                    if '?' in url_val:
                        base, params = url_val.split('?', 1)
                        param_dict = dict(p.split('=') for p in params.split('&'))
                        return url_for(base, **param_dict)
                    return url_for(url_val)
            except:
                pass
            return url_val

            
        nav_items = NavigationItem.query.filter_by(is_active=True).order_by(NavigationItem.display_order.asc()).all()
        return dict(nav_items=nav_items, resolve_url=resolve_url)

    return app
