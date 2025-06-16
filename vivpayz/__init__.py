from flask import Flask
from flask_jwt_extended import JWTManager
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from dotenv import load_dotenv
import os
from vivpayz.config import Config
from flask_cors import CORS

load_dotenv()

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()

def create_app():
    app = Flask(__name__)
    CORS(app, origins=["http://localhost:5173"], supports_credentials=True)


    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    from vivpayz.auth.routes import auth_bp  
    from vivpayz.user.routes import user_bp
    from vivpayz.wallet.routes import wallet_bp
    from vivpayz.card.routes import card_bp
    from vivpayz.payment.routes import paystack
    
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(user_bp)
    app.register_blueprint(wallet_bp)
    app.register_blueprint(card_bp)
    app.register_blueprint(paystack)
    return app
