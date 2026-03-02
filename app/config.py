import os

class Config:
    DATABASE_URL = os.getenv("DATABASE_URL")
    SECRET_KEY = os.getenv("SECRET_KEY", "dev")

    ENVIRONMENT = os.getenv("ENVIRONMENT", "production")

    PREFERRED_URL_SCHEME = "https"

    _BASE_URL_RAW = os.getenv("BASE_URL")
    BASE_URL = _BASE_URL_RAW.rstrip("/") if _BASE_URL_RAW else None

    # =========================
    # APP / BRAND (PWA + UI)
    # =========================
    APP_NAME = os.getenv("APP_NAME", "SMT Manager")
    APP_SHORT_NAME = os.getenv("APP_SHORT_NAME", "SMT Manager")
    APP_DESCRIPTION = os.getenv("APP_DESCRIPTION", "SMT Manager - Acesso corporativo")
    APP_THEME_COLOR = os.getenv("APP_THEME_COLOR", "#0f172a")
    APP_LANG = os.getenv("APP_LANG", "pt-BR")


    APP_VERSION = (
        os.getenv("APP_VERSION")
        or os.getenv("RAILWAY_GIT_COMMIT_SHA")
        or os.getenv("RAILWAY_GIT_COMMIT")
        or "dev"
    )

    # =========================
    # OPERACIONAL
    # =========================
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

    GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
    GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")

    # ==========================
    # SMTP CONFIG
    # ==========================
    SMTP_HOST = os.getenv("SMTP_HOST")
    SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
    SMTP_USERNAME = os.getenv("SMTP_USERNAME")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
    SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
    SMTP_FROM = os.getenv("SMTP_FROM")

    # ==========================
    # SENDGRID
    # ==========================
    SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
    SENDGRID_FROM = os.getenv("SENDGRID_FROM")
