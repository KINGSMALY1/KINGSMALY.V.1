import os


def _normalize_db_url(url):
    """
    Render (like Heroku before it) provides DATABASE_URL starting with
    postgres:// but modern SQLAlchemy requires postgresql://. Without
    this fix, the app crashes on startup in production.
    """
    if url and url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql://", 1)
    return url


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "change-me-in-production")

    SQLALCHEMY_DATABASE_URI = _normalize_db_url(
        os.environ.get("DATABASE_URL", "sqlite:///kingsmaly.db")
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    APP_BASE_URL = os.environ.get("APP_BASE_URL", "http://localhost:5000")

    # Paystack
    PAYSTACK_SECRET_KEY = os.environ.get("PAYSTACK_SECRET_KEY", "")
    PAYSTACK_BASE_URL = os.environ.get("PAYSTACK_BASE_URL", "https://api.paystack.co")

    # Grandstream GWN.Cloud - confirmed working auth: client_credentials grant
    GWN_CLOUD_BASE_URL = os.environ.get("GWN_CLOUD_BASE_URL", "https://www.gwn.cloud")
    GWN_APP_ID = os.environ.get("GWN_APP_ID", "")
    GWN_SECRET_KEY = os.environ.get("GWN_SECRET_KEY", "")
    GWN_NETWORK_ID = os.environ.get("GWN_NETWORK_ID", "")

    # Captive-portal login endpoint the AP redirects clients to. Used by
    # the "Use it on this device" option on the payment success page to
    # submit the voucher automatically instead of making the customer
    # retype it. Leave blank to fall back to manual entry.
    GWN_PORTAL_AUTH_URL = os.environ.get("GWN_PORTAL_AUTH_URL", "")

    # Celery
    CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")
    CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")
