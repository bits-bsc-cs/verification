from sqlalchemy import String, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from app.database import Base


class User(Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String, primary_key=True)
    uid: Mapped[str] = mapped_column(String)
    verified_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class PendingOTP(Base):
    __tablename__ = "pending_otps"

    email: Mapped[str] = mapped_column(String, primary_key=True)
    otp: Mapped[str] = mapped_column(String)
    expiry: Mapped[int] = mapped_column(Integer)
    last_request: Mapped[int] = mapped_column(Integer)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
