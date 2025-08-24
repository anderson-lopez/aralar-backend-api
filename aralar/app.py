from flask import Flask
from .config import get_config
from .extensions import init_extensions
from .api.routes import register_blueprints
from .docs.openapi import init_api_docs
from .core.loggin import setup_logging


def create_app(config_name="development"):
    app = Flask(__name__)
    app.config.from_object(get_config(config_name))
    setup_logging(app)
    init_api_docs(app)  # Mover antes de init_extensions
    init_extensions(app)
    register_blueprints(app)
    return app
