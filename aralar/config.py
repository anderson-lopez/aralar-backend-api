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
    # i18n / translation providers
    I18N_PROVIDER = os.getenv("I18N_PROVIDER", "deepl").lower()
    DEEPL_API_KEY = os.getenv("DEEPL_API_KEY", "")
    DEEPL_BASE_URL = os.getenv("DEEPL_BASE_URL", "https://api.deepl.com/v2")
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
    GOOGLE_BASE_URL = os.getenv("GOOGLE_BASE_URL", "https://translation.googleapis.com/language/translate/v2")
    # S3 / object storage
    S3_ENDPOINT = os.getenv("S3_ENDPOINT", "http://localhost:9000")
    S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY", "minio")
    S3_SECRET_KEY = os.getenv("S3_SECRET_KEY", "minio123")
    S3_REGION = os.getenv("S3_REGION", "us-east-1")
    S3_BUCKET = os.getenv("S3_BUCKET", "aralar-media")
    # seed defaults
    SEED_ADMIN_EMAIL = os.getenv("SEED_ADMIN_EMAIL", "admin@aralar.local")
    SEED_ADMIN_FULLNAME = os.getenv("SEED_ADMIN_FULLNAME", "Admin Aralar")
    SEED_ADMIN_PASSWORD = os.getenv("SEED_ADMIN_PASSWORD", "ChangeMeNow!2025")


class DevelopmentConfig(BaseConfig):
    DEBUG = True


class ProductionConfig(BaseConfig):
    TALISMAN_FORCE_HTTPS = True


def get_config(name):
    return {"development": DevelopmentConfig, "production": ProductionConfig}.get(
        name, DevelopmentConfig
    )
