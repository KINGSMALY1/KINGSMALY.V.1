from flask import Blueprint

from app.api.payment_routes import payment_bp
from app.api.webhook_routes import webhook_bp
from app.api.portal_routes import portal_api_bp

api_bp = Blueprint("api", __name__)

api_bp.register_blueprint(payment_bp, url_prefix="/payment")
api_bp.register_blueprint(webhook_bp, url_prefix="/webhook")
api_bp.register_blueprint(portal_api_bp, url_prefix="/portal")
