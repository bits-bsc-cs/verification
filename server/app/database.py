from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session

from app.cfg import settings


SQLALCHEMY_DATABASE_URL = f"{settings.db_type}:///{settings.db_location}"

if SQLALCHEMY_DATABASE_URL:
    print("sql db url checked")

engine = create_engine(SQLALCHEMY_DATABASE_URL)
if engine:
    print("sql db engine created")
    print(f"engine: {engine}")


class Base(DeclarativeBase):
    pass


def init_db():
    import app.models

    Base.metadata.create_all(bind=engine)

    with engine.connect() as conn:
        has_verified_at = False
        try:
            result = conn.execute(text("PRAGMA table_info('users');"))
            for row in result:
                if row[1] == "verified_at":
                    has_verified_at = True
                    break
        except Exception:
            pass

        if not has_verified_at:
            conn.execute(text("ALTER TABLE users ADD COLUMN verified_at DATETIME"))
            conn.commit()


def get_db():
    with Session(engine) as db_session:
        yield db_session
