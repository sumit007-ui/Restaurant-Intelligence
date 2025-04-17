import os
import logging

from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix
from extensions import db, login_manager

from dotenv import load_dotenv
load_dotenv()
# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)  # Needed for url_for to generate with https

# Configure the SQLite database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///restaurant.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize database
db.init_app(app)

# Initialize login manager
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'


def create_default_admin():
    """Create a default admin user if it doesn't exist."""
    from werkzeug.security import generate_password_hash
    from models import User

    admin = User.query.filter_by(role='admin').first()
    if not admin:
        admin = User(
            username='admin',
            email='admin@restaurant.com',
            password_hash=generate_password_hash('admin123'),
            role='admin'
        )
        db.session.add(admin)
        db.session.commit()
        logging.info("Created default admin user")


# Import models and routes here to avoid circular imports
with app.app_context():
    from models import User, Dish, DailyData  # Import models here
    from routes import setup_routes

    # Create database tables
    db.create_all()

    # Setup routes
    setup_routes(app)

    # Create default admin user
    create_default_admin()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)