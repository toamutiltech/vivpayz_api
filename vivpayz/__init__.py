from flask import Flask, send_from_directory
from flask_jwt_extended import JWTManager
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from dotenv import load_dotenv
from flask_mail import Mail
import os
from vivpayz.config import Config
from flask_cors import CORS

load_dotenv()

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
mail = Mail()

def create_app():
    app = Flask(__name__, static_url_path='/static')  # 👈 Correctly put static_url_path here

    # Enable CORS
    #CORS(app, origins=["http://localhost:5173"], supports_credentials=True)
    CORS(app, origins=["https://vivpayz-fintech.vercel.app", "https://vivpayz.tech"], supports_credentials=True)
    #app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://bizapplivecom_vivpay:Bk9!39[O*+Cb@localhost/bizapplivecom_vivpayz'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://vivpayz_dbuser:hURmixfC2NI91VlAH0DzuiYGMb0JwTWd@dpg-d36kee7diees73btn2m0-a/vivpayz_db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


    # Flask-Mail configuration
    app.config['MAIL_SERVER'] = os.getenv("SMTP_SERVER")
    app.config['MAIL_PORT'] = int(os.getenv("SMTP_PORT", 587))
    app.config['MAIL_USERNAME'] = os.getenv("SMTP_USERNAME")
    app.config['MAIL_PASSWORD'] = os.getenv("SMTP_PASSWORD")
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USE_SSL'] = False
    app.config['MAIL_DEFAULT_SENDER'] = os.getenv("SMTP_FROM")

    mail.init_app(app)

    # Load app config
    app.config.from_object(Config)

    # Init extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    #with app.app_context():
        #from vivpayz import models  # make sure this imports ALL your model classes

        # ⚠️ This will drop every table in your database
       # db.drop_all()


        # Recreate all tables using your SQLAlchemy models
        #db.create_all()



    # Register blueprints
    from vivpayz.auth.routes import auth_bp  
    from vivpayz.user.routes import user_bp
    from vivpayz.wallet.routes import wallet_bp
    from vivpayz.card.routes import card_bp
    from vivpayz.payment.routes import paystack
    from vivpayz.main.routes import main
    from vivpayz.convert.routes import convert_bp
    from vivpayz.transfer.routes import transfer_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(user_bp)
    app.register_blueprint(wallet_bp)
    app.register_blueprint(card_bp)
    app.register_blueprint(paystack)
    app.register_blueprint(main)
    app.register_blueprint(convert_bp)
    app.register_blueprint(transfer_bp)

    # 👇 Route to serve uploaded profile images
    @app.route('/static/uploads/<filename>')
    def uploaded_file(filename):
        return send_from_directory('static/uploads', filename)

    return app
