import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'orial-secret-key-2025-jewellery')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///orial.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app', 'static', 'images')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    FREE_SHIPPING_THRESHOLD = 200.00
    WTF_CSRF_ENABLED = True
