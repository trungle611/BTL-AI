import os
import uuid
from pathlib import Path
from dotenv import load_dotenv
from fastapi import HTTPException, Request
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.pool import NullPool
from sqlalchemy.orm import DeclarativeBase, sessionmaker


class Base(DeclarativeBase):
    pass


load_dotenv(Path(__file__).resolve().parents[1] / ".env")
DATABASE_URL = os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL") or "sqlite:///./hbtnfit.db"
if os.getenv("VERCEL") and DATABASE_URL.startswith("sqlite"):
    raise RuntimeError("Vercel cần DATABASE_URL hoặc POSTGRES_URL dùng PostgreSQL")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = "postgresql://" + DATABASE_URL[len("postgres://"):]
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = "postgresql+psycopg://" + DATABASE_URL[len("postgresql://"):]
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
                       **({"poolclass": NullPool, "pool_pre_ping": True} if DATABASE_URL.startswith("postgresql") else {}))
SessionLocal = sessionmaker(bind=engine)


def migrate_demo_columns():
    """Add columns to existing local SQLite demo databases without losing entries."""
    if not DATABASE_URL.startswith("sqlite"):
        return
    columns = {"foods": {"display_name": "VARCHAR(160)", "owner_id": "VARCHAR(40)"},
               "profiles": {"visitor_id": "VARCHAR(40)", "sex": "VARCHAR(10)", "activity_level": "VARCHAR(20)", "protein_mode": "VARCHAR(20)"},
               "profile_guidance": {"visitor_id": "VARCHAR(40)", "target_date": "VARCHAR(10)"},
               "food_logs": {"visitor_id": "VARCHAR(40)"},
               "meal_plans": {"visitor_id": "VARCHAR(40)"},
               "workout_selection": {"visitor_id": "VARCHAR(40)"}}
    inspector = inspect(engine)
    with engine.begin() as connection:
        for table, fields in columns.items():
            if not inspector.has_table(table):
                continue
            existing = {column["name"] for column in inspector.get_columns(table)}
            for name, type_name in fields.items():
                if name not in existing:
                    connection.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {type_name}"))


def get_db(request: Request):
    raw = request.headers.get("X-Visitor-Id")
    if not raw and os.getenv("REQUIRE_VISITOR_ID") == "1":
        raise HTTPException(400, "Thiếu mã phiên dùng thử")
    try:
        visitor = str(uuid.UUID(raw)) if raw else "demo-local"
    except ValueError as exc:
        raise HTTPException(400, "Mã phiên dùng thử không hợp lệ") from exc
    with SessionLocal() as session:
        session.info["visitor_id"] = visitor
        yield session

