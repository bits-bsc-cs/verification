from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import select, delete
from fastapi import Depends, FastAPI, HTTPException, status, Form
from typing import Annotated
import random
import string
import resend
import time
import asyncio
from datetime import datetime
from contextlib import asynccontextmanager
from sqlalchemy.orm import Session

from .database import get_db, init_db, engine
from . import bot, models
from .cfg import settings


async def cleanup_expired_otps():
    """OTP cleaning from sqlite because idk Redis"""
    while True:
        try:
            with Session(engine) as db:
                now = int(time.time())
                db.execute(
                    delete(models.PendingOTP).where(models.PendingOTP.expiry < now)
                )
                db.commit()
        except Exception as e:
            print(f"Cleanup task error: {e}")
        await asyncio.sleep(3600)  # Run every hour


@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(cleanup_expired_otps())
    yield


app = FastAPI(lifespan=lifespan)


init_db()

cors_origins = settings.allowed_cors_origins.split(",")

origin = settings.allowed_cors_origin
if origin:
    cors_origins = list({*cors_origins, origin})

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/verify")
def verification_request(
    email: Annotated[str, Form()],
    username: Annotated[str, Form()],
    db: Session = Depends(get_db),
):
    # Check if email already used for verification
    existing_user = db.scalars(
        select(models.User).where(models.User.email == email)
    ).first()

    if existing_user:
        raise HTTPException(status_code=400, detail="Email already verified")

    now = int(time.time())

    # Rate Limiting
    existing_otp = db.scalars(
        select(models.PendingOTP).where(models.PendingOTP.email == email)
    ).first()

    if existing_otp:
        if now - existing_otp.last_request < 60:  # 1 minute cooldown
            raise HTTPException(
                status_code=429,
                detail="Please wait 1 minute before requesting another OTP",
            )

    # Email Suffix Check (depends on prod settings set in env file)
    if settings.production:
        allowed_domains = (
            "online.bits-pilani.ac.in",
            "pilani.bits-pilani.ac.in",
            "hyderabad.bits-pilani.ac.in",
            "goa.bits-pilani.ac.in",
            "dubai.bits-pilani.ac.in",
        )
        email_domain = email.lower().split("@")[-1]
        if email_domain not in allowed_domains:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Email must end with @online.bits-pilani.ac.in, "
                    "@pilani.bits-pilani.ac.in, @hyderabad.bits-pilani.ac.in, "
                    "@goa.bits-pilani.ac.in, or @dubai.bits-pilani.ac.in"
                ),
            )

    otp_code = "".join(random.choices(string.digits, k=6))
    expiry_time = now + (settings.otp_expiry_mins * 60)

    # Update or create pending OTP in DB
    new_otp = models.PendingOTP(
        email=email, otp=otp_code, expiry=expiry_time, last_request=now, attempts=0
    )
    db.merge(new_otp)
    db.commit()

    resend.api_key = settings.resend_key

    try:
        email_params: resend.Emails.SendParams = {
            "from": settings.sender_email,
            "to": [email],
            "subject": "Your Verification OTP",
            "html": f"<strong>Your OTP is: {otp_code}</strong>",
        }

        # Log OTP for debugging (if env set to not prod)
        if not settings.production:
            print(f"DEBUG: Generated OTP for {email}: {otp_code}")
            with open("otp_debug.log", "a") as f:
                f.write(f"{email}: {otp_code}\n")

        resend.Emails.send(email_params)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")

    return {"message": "OTP sent successfully"}


@app.get("/verify/status/{email}")
def get_status(email: str, db: Session = Depends(get_db)):
    # Check if verified
    user = db.scalars(select(models.User).where(models.User.email == email)).first()
    if user:
        return {
            "status": "verified",
            "uid": user.uid,
            "verified_at": user.verified_at.isoformat() if user.verified_at else None,
        }

    # Check if pending
    pending = db.scalars(
        select(models.PendingOTP).where(models.PendingOTP.email == email)
    ).first()
    if pending:
        # Check if expired
        if int(time.time()) > pending.expiry:
            db.delete(pending)
            db.commit()
            return {"status": "not_found"}

        return {"status": "pending", "expiry": pending.expiry}

    return {"status": "not_found"}


@app.post("/verify/otp")
def verify_otp(
    email: Annotated[str, Form()],
    username: Annotated[str, Form()],
    db: Session = Depends(get_db),
    otp: str = Form(...),
):
    if not otp:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect OTP!"
        )

    stored_otp = db.scalars(
        select(models.PendingOTP).where(models.PendingOTP.email == email)
    ).first()

    if not stored_otp:
        raise HTTPException(status_code=400, detail="No OTP requested for this email")

    if int(time.time()) > stored_otp.expiry:
        db.delete(stored_otp)
        db.commit()
        raise HTTPException(status_code=400, detail="OTP has expired")

    if stored_otp.otp == otp:
        print("OTP is correct")

        uid = bot.verify(username)

        if uid:
            # Check if this Discord UID is already linked to another email
            existing_uid = db.query(models.User).filter(models.User.uid == uid).first()
            if existing_uid:
                raise HTTPException(
                    status_code=400,
                    detail="Discord account already linked to another email",
                )

            # Create User and record verification time
            user = models.User(email=email, uid=uid, verified_at=datetime.utcnow())
            db.merge(user)

            # Remove the OTP after successful verification
            db.delete(stored_otp)

            db.commit()
            return {"message": "OTP is correct, user verified on Discord"}
        else:
            raise HTTPException(status_code=500, detail="Failed to verify Discord user")

    else:
        print("OTP is incorrect")
        stored_otp.attempts += 1
        db.commit()

        if stored_otp.attempts >= 5:
            db.delete(stored_otp)
            db.commit()
            raise HTTPException(
                status_code=400,
                detail="Too many failed attempts. Please request a new OTP.",
            )

        return {
            "message": f"OTP is incorrect. {5 - stored_otp.attempts} attempts remaining."
        }
