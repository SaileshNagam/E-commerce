from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from urllib.parse import quote_plus
from models import db, CartItem, Cart, Product

# Database configuration
import os
DB_USER = os.environ.get('DB_USER', 'root')
DB_PASSWORD = quote_plus(os.environ.get('DB_PASSWORD', 'your_password_here'))  # URL encode the password
DB_HOST = os.environ.get('DB_HOST', '127.0.0.1')
DB_PORT = os.environ.get('DB_PORT', '3306')
DB_NAME = os.environ.get('DB_NAME', 'ecommerce')

def create_tables():
    try:
        # Create Flask app
        app = Flask(__name__)
        app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        
        # Initialize SQLAlchemy with app
        db.init_app(app)
        
        # Create tables
        with app.app_context():
            db.create_all()
            print("Tables created successfully!")

    except Exception as err:
        print(f"Error: {err}")

if __name__ == "__main__":
    create_tables() 