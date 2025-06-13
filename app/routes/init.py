from flask import Flask
from flask_jwt_extended import JWTManager
from app.routes import register_routes
from .wallet import wallet_bp
from .auth   import auth_bp

jwt = JWTManager()

def create_app():
    app = Flask(__name__)
    app.config.from_object("app.config.Config")

    # init JWT
    jwt.init_app(app)

    # register your other blueprints
    
def register_routes(app):
    app.register_blueprint(auth_bp)
    app.register_blueprint(wallet_bp, url_prefix="/api/wallet")

    return app
