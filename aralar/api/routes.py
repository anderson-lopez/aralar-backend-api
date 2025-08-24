from .auth.blueprint import blp as auth_blp
from .users.blueprint import blp as users_blp
from flask_smorest import Api


def register_blueprints(app):
    # Crear instancia Api con la app ya configurada
    api = Api(app)
    
    # Registrar blueprints
    api.register_blueprint(auth_blp, url_prefix="/api/auth")
    api.register_blueprint(users_blp, url_prefix="/api/users")
    
    # Almacenar referencia para debugging
    app.api = api
