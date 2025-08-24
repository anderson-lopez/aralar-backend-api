import os


class BaseConfig:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev")
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/aralar")
    API_TITLE = "Aralar API"
    API_VERSION = "1.0.0"
    OPENAPI_VERSION = "3.0.3"
    CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",")]
    RATELIMIT_DEFAULT = os.getenv("RATE_LIMIT_DEFAULT", "100/hour")
    TALISMAN_FORCE_HTTPS = False


class DevelopmentConfig(BaseConfig):
    DEBUG = True


class ProductionConfig(BaseConfig):
    TALISMAN_FORCE_HTTPS = True


def get_config(name):
    return {"development": DevelopmentConfig, "production": ProductionConfig}.get(
        name, DevelopmentConfig
    )
