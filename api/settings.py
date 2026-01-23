from pydantic_settings import BaseSettings
from functools import lru_cache
from pathlib import Path


class Settings(BaseSettings):
    WIX_API_KEY: str
    WIX_ACCOUNT_ID: str
    WIX_SITE_ID: str
    WIX_APP_ID:str
    WIX_APP_SECRET:str
    WIX_PUBLIC_KEY:str

    BREVO_API_KEY: str
    BREVO_API_URL: str = "https://api.brevo.com/v3/smtp/email"
    BREVO_SENDER_EMAIL: str
    BREVO_SENDER_NAME: str = "Hoops"

    CORS_ORIGIN: str = "http://localhost:3000"
    FRONTEND_URL: str = "http://localhost:3000"
    DEPLOYMENT_ENVIRONMENT: str = "PROD"
    COOLDOWN_RESEND_VERIFICATION_MAIL_MINUTES:int = 5
    ACCESS_EXPIRE_MINUTES: int = 15
    REFRESH_EXPIRE_DAYS: int = 7
    AUTH_SECRET_KEY: str
    AUTH_ALGORITM: str
    DATABASE_URL: str

    @property
    def HTTP_ONLY_COOKIE_SECURE(self):
        return self.DEPLOYMENT_ENVIRONMENT != "DEV"

    @property
    def SWAGGER_ACTIVE(self):
        return self.DEPLOYMENT_ENVIRONMENT == "DEV"

    @property
    def SCHEDULER_ACTIVE(self):
        return self.DEPLOYMENT_ENVIRONMENT == "DEV"

    class Config:
        env_file = Path(__file__).resolve().parent.parent / ".env"


@lru_cache()
def get_settings():
    settings = Settings()
    return settings
