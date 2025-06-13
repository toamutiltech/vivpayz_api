from .wallet import wallet_bp

def register_routes(app):
    app.register_blueprint(wallet_bp, url_prefix="/api/wallet")
