from datetime import datetime, timezone
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .db import Base


def utcnow():
    return datetime.now(timezone.utc)


class Food(Base):
    __tablename__ = "foods"
    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    name: Mapped[str] = mapped_column(String(160), unique=True)
    kcal_100g: Mapped[float] = mapped_column(Float)
    protein_100g: Mapped[float] = mapped_column(Float)
    carb_100g: Mapped[float] = mapped_column(Float)
    fat_100g: Mapped[float] = mapped_column(Float)
    source_type: Mapped[str] = mapped_column(String(40))
    source_reference: Mapped[str] = mapped_column(Text)
    reference_mass_g: Mapped[float] = mapped_column(Float, default=100)
    data_version: Mapped[str] = mapped_column(String(40))
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    avoid_tags: Mapped[list] = mapped_column(JSON, default=list)
    aliases: Mapped[list["FoodAlias"]] = relationship(back_populates="food", cascade="all, delete-orphan")


class FoodAlias(Base):
    __tablename__ = "food_aliases"
    __table_args__ = (UniqueConstraint("food_id", "alias"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    food_id: Mapped[str] = mapped_column(ForeignKey("foods.id"))
    alias: Mapped[str] = mapped_column(String(160))
    food: Mapped[Food] = relationship(back_populates="aliases")


class Profile(Base):
    __tablename__ = "profiles"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height_cm: Mapped[float | None] = mapped_column(Float, nullable=True)
    weight_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    goal: Mapped[str] = mapped_column(String(20), default="maintain")
    avoid_tags: Mapped[list] = mapped_column(JSON, default=list)
    target_kcal: Mapped[float] = mapped_column(Float, default=1800)


class FoodLog(Base):
    __tablename__ = "food_logs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    food_id: Mapped[str] = mapped_column(ForeignKey("foods.id"))
    grams: Mapped[float] = mapped_column(Float)
    meal_type: Mapped[str] = mapped_column(String(30))
    eaten_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    food: Mapped[Food] = relationship()


class MealPlan(Base):
    __tablename__ = "meal_plans"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    week_start: Mapped[str] = mapped_column(String(10))
    target_kcal: Mapped[float] = mapped_column(Float)
    avoid_tags: Mapped[list] = mapped_column(JSON, default=list)
    generation_mode: Mapped[str] = mapped_column(String(40))
    model_version: Mapped[str] = mapped_column(String(80))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    items: Mapped[list["MealPlanItem"]] = relationship(back_populates="plan", cascade="all, delete-orphan")


class MealPlanItem(Base):
    __tablename__ = "meal_plan_items"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    plan_id: Mapped[int] = mapped_column(ForeignKey("meal_plans.id"))
    day: Mapped[int] = mapped_column(Integer)
    meal_slot: Mapped[str] = mapped_column(String(20))
    food_id: Mapped[str] = mapped_column(ForeignKey("foods.id"))
    grams: Mapped[float] = mapped_column(Float)
    plan: Mapped[MealPlan] = relationship(back_populates="items")
    food: Mapped[Food] = relationship()


class AiRun(Base):
    __tablename__ = "ai_runs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    purpose: Mapped[str] = mapped_column(String(30))
    prompt_version: Mapped[str] = mapped_column(String(40))
    model_id: Mapped[str] = mapped_column(String(80))
    latency_ms: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(30))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class WorkoutProgress(Base):
    __tablename__ = "workout_progress"
    __table_args__ = (UniqueConstraint("workout_id", "day"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    workout_id: Mapped[str] = mapped_column(String(40))
    day: Mapped[str] = mapped_column(String(10))
    status: Mapped[str] = mapped_column(String(20), default="not_started")
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class WorkoutSelection(Base):
    __tablename__ = "workout_selection"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    plan_id: Mapped[str] = mapped_column(String(40))


class BatchSubmission(Base):
    __tablename__ = "batch_submissions"
    confirmation_id: Mapped[str] = mapped_column(String(80), primary_key=True)
    request_hash: Mapped[str] = mapped_column(String(64))
    log_ids: Mapped[list] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
