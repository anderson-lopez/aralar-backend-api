from .auth.blueprint import blp as auth_blp
from .users.blueprint import blp as users_blp
from .roles.blueprint import blp as roles_blp
from .menus.blueprint import blp as menus_blp
from .menu_templates.blueprint import blp as menu_templates_blp
from .menu_services.blueprint import blp as menu_services_blp
from .google_reviews.blueprint import blp as google_reviews_blp
from .uploads.blueprint import blp as uploads_blp
from .i18n.blueprint import blp as i18n_blp
from .catalogs.blueprint import blp as catalogs_blp
from .notifications.blueprint import blp as notifications_blp
from flask_smorest import Api


def register_blueprints(app):
    # Crear instancia Api con la app ya configurada
    api = Api(app)

    # Registrar blueprints
    api.register_blueprint(auth_blp, url_prefix="/api/auth")
    api.register_blueprint(users_blp, url_prefix="/api/users")
    api.register_blueprint(roles_blp, url_prefix="/api/roles")
    api.register_blueprint(menus_blp, url_prefix="/api/menus")
    api.register_blueprint(menu_templates_blp, url_prefix="/api/menu-templates")
    api.register_blueprint(menu_services_blp, url_prefix="/api/menu-services")
    api.register_blueprint(google_reviews_blp, url_prefix="/api/google-reviews")
    api.register_blueprint(uploads_blp, url_prefix="/api/uploads")
    api.register_blueprint(i18n_blp, url_prefix="/api/i18n")
    api.register_blueprint(catalogs_blp, url_prefix="/api/catalogs")
    api.register_blueprint(notifications_blp, url_prefix="/api/notifications")
   

    # Almacenar referencia para debugging
    app.api = api
