from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_limiter import Limiter
from flask_talisman import Talisman
from pymongo import MongoClient
from flask_jwt_extended import get_jwt_identity
from flask import request


def _rate_limit_key():
    try:
        # Si hay JWT válido, usa el usuario; si no, usa IP
        return get_jwt_identity() or request.remote_addr
    except Exception:
        return request.remote_addr


jwt = JWTManager()
limiter = Limiter(key_func=_rate_limit_key)
talisman = Talisman()
mongo_client = None


def init_extensions(app):
    global mongo_client
    # DB
    mongo_client = MongoClient(app.config["MONGO_URI"])
    app.mongo_db = mongo_client.get_default_database()

    # Seguridad y control
    jwt.init_app(app)
    limiter.init_app(app)
    CORS(app, resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}})
    
    # Configurar CSP para permitir Swagger UI CDN
    csp = {
        'default-src': "'self'",
        'style-src': [
            "'self'",
            "'unsafe-inline'",
            "https://cdn.jsdelivr.net"
        ],
        'script-src': [
            "'self'",
            "'unsafe-inline'",
            "https://cdn.jsdelivr.net"
        ],
        'img-src': [
            "'self'",
            "data:",
            "https://cdn.jsdelivr.net"
        ],
        'font-src': [
            "'self'",
            "https://cdn.jsdelivr.net"
        ]
    }
    
    talisman.init_app(
        app, 
        force_https=app.config.get("TALISMAN_FORCE_HTTPS", False),
        content_security_policy=csp
    )
