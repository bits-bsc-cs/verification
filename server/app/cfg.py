import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

if not load_dotenv():
    load_dotenv("../.env")


class Settings(BaseSettings):
    db_type: str = os.getenv("DATABASE_TYPE") or "sqlite"
    db_location: str = os.getenv("DATABASE_LOCATION") or "db.sqlite3"
    discord_token: str = os.getenv("DISCORD_TOKEN") or ""
    resend_key: str = os.getenv("RESEND_API_KEY") or ""
    discord_role_name: str = os.getenv("DISCORD_ROLE_NAME") or "human"
    discord_guild_id: str = os.getenv("DISCORD_GUILD_ID") or ""
    otp_expiry_mins: int = 10
    production: bool = os.getenv("PRODUCTION", "false").lower() == "true"
    allowed_cors_origins: str = os.getenv(
        "ALLOWED_CORS_ORIGINS", "http://localhost,http://localhost:5000"
    )
    allowed_cors_origin: str = os.getenv("ALLOWED_CORS_ORIGIN", "")
    ipc_secret: str = os.getenv("IPC_SECRET") or "default_secret"
    sender_email: str = (
        os.getenv("SENDER_EMAIL") or "Verification <onboarding@resend.dev>"
    )


settings = Settings()
