from .auth.blueprint import blp as auth_blp
from .users.blueprint import blp as users_blp
from .menus.blueprint import blp as menus_blp
from .menu_templates.blueprint import blp as menu_templates_blp
from flask_smorest import Api


def register_blueprints(app):
    # Crear instancia Api con la app ya configurada
    api = Api(app)

    # Registrar blueprints
    api.register_blueprint(auth_blp, url_prefix="/api/auth")
    api.register_blueprint(users_blp, url_prefix="/api/users")
    api.register_blueprint(menus_blp, url_prefix="/api/menus")
    api.register_blueprint(menu_templates_blp, url_prefix="/api/menu-templates")

    # Almacenar referencia para debugging
    app.api = api
