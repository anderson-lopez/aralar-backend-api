"""
Fixtures globales de pytest para la test suite de Aralar API.

Este archivo es auto-descubierto por pytest y sus fixtures están disponibles
en todos los archivos `test_*.py` sin necesidad de importar nada.

Estrategia:
- Reemplazamos MongoDB real por `mongomock` (Mongo en memoria) antes de
  crear la app, así `create_app()` no intenta conectar a un Mongo real.
- Creamos una app Flask por cada test (scope="function") para garantizar
  aislamiento total: cada test empieza con una DB vacía y limpia.
- Proveemos helpers de autenticación (`auth_headers`) que generan JWTs
  válidos vinculados a un usuario real en mongomock.

Fixtures expuestas:
- `app`           → instancia de Flask con mongomock ya parcheado
- `client`        → test client HTTP para hacer GET/POST (tests E2E)
- `db`            → referencia directa a la DB mongomock (tests de integración)
- `auth_headers`  → factory que crea un usuario + devuelve headers con JWT
- `mongo_patch`   → (interna) parchea MongoClient antes de create_app
"""
import os
import pytest
import mongomock


# -----------------------------------------------------------------------------
# Setup de entorno (se ejecuta UNA vez antes de cargar la app)
# -----------------------------------------------------------------------------
# Fijamos variables de entorno necesarias para que `create_app` no falle
# buscando secretos reales. Se aplican antes de cualquier import de la app.
os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ.setdefault("JWT_SECRET_KEY", "test-jwt-secret")
os.environ.setdefault("MONGO_URI", "mongodb://localhost:27017/aralar_test")
os.environ.setdefault("CORS_ORIGINS", "*")


# -----------------------------------------------------------------------------
# Parche de MongoClient → mongomock
# -----------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def mongo_patch(monkeypatch):
    """
    Parchea `pymongo.MongoClient` en `aralar.extensions` para que cualquier
    `create_app()` use mongomock en vez de conectarse a un Mongo real.

    `autouse=True` hace que se aplique automáticamente a TODOS los tests,
    así no hay que recordarlo en cada fixture/caso.
    """
    monkeypatch.setattr("aralar.extensions.MongoClient", mongomock.MongoClient)
    yield


# -----------------------------------------------------------------------------
# App Flask (por test, aislada)
# -----------------------------------------------------------------------------
@pytest.fixture
def app(mongo_patch):
    """
    Crea una instancia de Flask con:
    - MongoDB parcheado a mongomock (vía `mongo_patch`)
    - Rate limiter desactivado (evita falsos 429 en tests)
    - Talisman sin forzar HTTPS
    - TESTING=True (Flask desactiva catching de errores, propaga excepciones)
    """
    from aralar.app import create_app

    app = create_app(config_name="development")
    app.config["TESTING"] = True
    app.config["RATELIMIT_ENABLED"] = False  # ← evita 429 en suites grandes
    app.config["TALISMAN_FORCE_HTTPS"] = False

    # Desactivar rate limiter a nivel de extensión (doble seguro)
    from aralar.extensions import limiter
    limiter.enabled = False

    yield app


@pytest.fixture
def client(app):
    """Test client HTTP de Flask para tests E2E (`client.get`, `client.post`, ...)."""
    return app.test_client()


@pytest.fixture
def db(app):
    """
    Acceso directo a la DB mongomock subyacente.

    Úsalo en tests de integración cuando necesites sembrar datos manualmente
    o verificar el estado de una colección después de un request.

    Ejemplo:
        def test_create_menu_persists_in_db(client, db, auth_headers):
            client.post("/api/menus", json={...}, headers=auth_headers())
            assert db["menus"].count_documents({}) == 1
    """
    return app.mongo_db


# -----------------------------------------------------------------------------
# Autenticación
# -----------------------------------------------------------------------------
@pytest.fixture
def auth_headers(app, db):
    """
    Factory fixture: devuelve una FUNCIÓN que crea un usuario en la DB
    (si no existe) y devuelve headers HTTP con un JWT válido para ese usuario.

    Uso simple (usuario admin con todos los permisos):
        def test_protected_endpoint(client, auth_headers):
            res = client.get("/api/menus", headers=auth_headers())
            assert res.status_code == 200

    Uso con permisos específicos:
        def test_forbidden_without_permission(client, auth_headers):
            res = client.get("/api/menus", headers=auth_headers(permissions=["other:perm"]))
            assert res.status_code == 403

    Uso con email custom (varios usuarios en el mismo test):
        headers_admin = auth_headers(email="admin@test.com", permissions=["menus:create"])
        headers_user  = auth_headers(email="user@test.com",  permissions=["menus:read"])

    Parámetros:
        email: str        — identificador del usuario (default: "test@aralar.local")
        permissions: list — lista de strings tipo "menus:read". Default: TODOS los permisos conocidos.
        roles: list       — lista de role codes. Default: ["admin"].
    """
    from bson import ObjectId
    from flask_jwt_extended import create_access_token

    # Permisos más comunes del sistema. Si tu módulo usa uno nuevo, agrégalo aquí.
    DEFAULT_PERMISSIONS = [
        "menus:create", "menus:read", "menus:update", "menus:delete", "menus:publish",
        "menu-templates:create", "menu-templates:read", "menu-templates:update", "menu-templates:delete",
        "users:create", "users:read", "users:update", "users:delete",
        "roles:read", "roles:update",
        "notifications:read", "notifications:create",
        "uploads:create",
    ]

    def _make(email: str = "test@aralar.local",
              permissions: list | None = None,
              roles: list | None = None) -> dict:
        permissions = permissions if permissions is not None else DEFAULT_PERMISSIONS
        roles = roles if roles is not None else ["admin"]

        # Crea el usuario en mongomock si no existe
        user = db["users"].find_one({"email": email})
        if not user:
            user_id = db["users"].insert_one({
                "email": email,
                "full_name": "Test User",
                "password_hash": "not-used-in-tests",
                "active": True,
                "roles": roles,
                "permissions_allow": permissions,
                "permissions_deny": [],
                "perm_version": 1,
            }).inserted_id
        else:
            user_id = user["_id"]

        # Genera el JWT dentro de un app_context (create_access_token lo requiere)
        with app.app_context():
            token = create_access_token(
                identity=str(user_id),
                additional_claims={
                    "roles": roles,
                    "permissions": permissions,
                    "email": email,
                    "perm_v": 1,
                },
            )

        return {"Authorization": f"Bearer {token}"}

    return _make
