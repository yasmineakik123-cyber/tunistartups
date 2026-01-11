import os
from urllib.parse import quote_plus

class Config:
    # FLASK
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
    PROPAGATE_EXCEPTIONS = True

    # DB (MySQL) - unrelated to Swagger
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = quote_plus(os.getenv("DB_PASSWORD", "YasmineAPI123"))
    DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
    DB_PORT = os.getenv("DB_PORT", "3306")
    DB_NAME = os.getenv("DB_NAME", "tunistartups")

    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # JWT (keep only ONE)
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "jwt-dev-secret-change-me")

    # FLASK-SMOREST / SWAGGER
    API_TITLE = "TuniStartups API"
    API_VERSION = "v1"
    OPENAPI_VERSION = "3.0.3"

    # IMPORTANT: keep at root (like before)
    OPENAPI_URL_PREFIX = "/"

    # Swagger UI path (open WITHOUT trailing slash)
    OPENAPI_SWAGGER_UI_PATH = "/swagger-ui"
    OPENAPI_SWAGGER_UI_URL = "https://cdn.jsdelivr.net/npm/swagger-ui-dist@4/"
    # app/config.py
import os
from urllib.parse import quote_plus

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")

    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = quote_plus(os.getenv("DB_PASSWORD", "YasmineAPI123"))
    DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
    DB_PORT = os.getenv("DB_PORT", "3306")
    DB_NAME = os.getenv("DB_NAME", "tunistartups")

    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "jwt-dev-secret-change-me")

    PROPAGATE_EXCEPTIONS = True
    API_TITLE = "TuniStartups API"
    API_VERSION = "v1"
    OPENAPI_VERSION = "3.0.3"
    OPENAPI_URL_PREFIX = "/"
    OPENAPI_SWAGGER_UI_PATH = "/swagger-ui"
    OPENAPI_SWAGGER_UI_URL = "https://cdn.jsdelivr.net/npm/swagger-ui-dist@4/"

    # ✅ Calendarific (Holiday API)
    CALENDARIFIC_API_KEY = os.getenv("CALENDARIFIC_API_KEY", "uiGRcN4IqZnG2gMBpXg8ZV6kmCxMqncz")
    CALENDARIFIC_COUNTRY = os.getenv("CALENDARIFIC_COUNTRY", "TN")
    CALENDARIFIC_BASE_URL = "https://calendarific.com/api/v2"
