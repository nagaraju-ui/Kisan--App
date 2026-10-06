import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

URL = os.getenv("DATABASE_URL", "postgresql+psycopg://kisan:kisan@localhost:5432/kisan")
engine = create_engine(URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False)

class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
