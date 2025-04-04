from flask import Flask
from app import routes
from app.models import db
from config import Config
from flask_login import LoginManager
from app.models import User
from datetime import datetime

login_manager = LoginManager()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    @app.context_processor
    def inject_now():
        return {'now': datetime.utcnow()}

    # Register blueprints
    app.register_blueprint(routes.main_bp)
    app.register_blueprint(routes.api_bp, url_prefix='/api')

    return app
