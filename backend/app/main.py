import os
import uuid
from time import perf_counter
from contextlib import asynccontextmanager
from datetime import date, datetime, timezone
from io import BytesIO
from PIL import Image, UnidentifiedImageError
from fastapi import Depends, FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload
from . import ai
from .core import fallback_plan, match_foods, normalize, nutrition, validate_plan
from .db import Base, engine, get_db
from .models import AiRun, Food, FoodAlias, FoodLog, MealPlan, MealPlanItem, Profile

@asynccontextmanager
async def lifespan(app):
    Base.metadata.create_all(engine)
    yield


app = FastAPI(title="HBTNFIT API", version="0.1.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"], allow_methods=["*"], allow_headers=["*"])


def food_data(food):
    return {"id": food.id, "name": food.name, "kcal_100g": food.kcal_100g,
            "protein_100g": food.protein_100g, "carb_100g": food.carb_100g,
            "fat_100g": food.fat_100g, "source_type": food.source_type,
            "source_reference": food.source_reference, "reference_mass_g": food.reference_mass_g,
            "data_version": food.data_version, "is_verified": food.is_verified,
            "avoid_tags": food.avoid_tags or [], "aliases": [a.alias for a in food.aliases]}


@app.get("/api/health")
def health():
    return {"status": "ok", "ai_configured": bool(os.getenv("GEMINI_API_KEY"))}


class ProfileIn(BaseModel):
    age: int | None = Field(default=None, ge=18, le=120)
    height_cm: float | None = Field(default=None, ge=100, le=250)
    weight_kg: float | None = Field(default=None, ge=25, le=400)
    goal: str = Field(default="maintain", pattern="^(maintain|gain|lose)$")
    avoid_tags: list[str] = []
    target_kcal: float = Field(default=1800, ge=900, le=5000)


def profile_data(profile):
    return {"age": profile.age, "height_cm": profile.height_cm,
            "weight_kg": profile.weight_kg, "goal": profile.goal,
            "avoid_tags": profile.avoid_tags or [], "target_kcal": profile.target_kcal}


@app.get("/api/profile")
def get_profile(db: Session = Depends(get_db)):
    profile = db.get(Profile, 1)
    return profile_data(profile) if profile else ProfileIn().model_dump()


@app.put("/api/profile")
def save_profile(payload: ProfileIn, db: Session = Depends(get_db)):
    profile = db.get(Profile, 1) or Profile(id=1)
    for key, value in payload.model_dump().items():
        setattr(profile, key, value)
    db.add(profile)
    db.commit()
    return profile_data(profile)


@app.get("/api/foods")
def foods(q: str = "", db: Session = Depends(get_db)):
    records = db.scalars(select(Food).options(selectinload(Food.aliases))).all()
    if q:
        query = normalize(q)
        records = [f for f in records if any(query in normalize(n) for n in [f.name] + [a.alias for a in f.aliases])]
    return [food_data(f) for f in records[:50]]


@app.get("/api/foods/{food_id}")
def get_food(food_id: str, db: Session = Depends(get_db)):
    food = db.scalar(select(Food).where(Food.id == food_id).options(selectinload(Food.aliases)))
    if not food:
        raise HTTPException(404, "Không tìm thấy món")
    return food_data(food)


@app.post("/api/scan")
async def scan(file: UploadFile = File(...), db: Session = Depends(get_db)):
    request_id = str(uuid.uuid4())
    raw = await file.read(5 * 1024 * 1024 + 1)
    if len(raw) > 5 * 1024 * 1024:
        raise HTTPException(413, "Ảnh vượt quá 5 MB")
    if file.content_type not in {"image/jpeg", "image/png", "image/webp"}:
        raise HTTPException(415, "Chỉ hỗ trợ JPG, PNG, WEBP")
    try:
        with Image.open(BytesIO(raw)) as image:
            image.verify()
    except (UnidentifiedImageError, OSError):
        raise HTTPException(422, "File ảnh không hợp lệ")
    started = perf_counter()
    status = "ok"
    try:
        result = ai.scan_image(raw, file.content_type)
    except RuntimeError as exc:
        status = "not_configured"
        raise HTTPException(503, str(exc))
    except Exception:
        status = "service_error"
        raise HTTPException(503, "Dịch vụ nhận diện tạm thời không khả dụng")
    finally:
        db.add(AiRun(purpose="scan", prompt_version=ai.SCAN_PROMPT_VERSION,
                     model_id=os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite"),
                     latency_ms=round((perf_counter() - started) * 1000), status=status))
        db.commit()
    records = db.scalars(select(Food).options(selectinload(Food.aliases))).all()
    candidates = match_foods(result.get("candidate_labels", [])[:3], records)
    return {"request_id": request_id, "status": "needs_confirmation" if candidates else "unknown",
            "candidates": [food_data(f) for f in candidates],
            "portion_hint": result.get("portion_hint", "unknown"),
            "visible_ingredients": result.get("visible_ingredients", []),
            "warnings": ["Khẩu phần ảnh chỉ là gợi ý; hãy xác nhận số gam."] +
                        ([result.get("uncertainty_reason")] if result.get("uncertainty_reason") else []),
            "prompt_version": ai.SCAN_PROMPT_VERSION}


class LogIn(BaseModel):
    food_id: str
    grams: float = Field(gt=0, le=2000)
    meal_type: str = Field(pattern="^(breakfast|lunch|dinner|snack)$")
    eaten_at: datetime | None = None
    confirmed: bool


@app.post("/api/food-logs", status_code=201)
def add_log(payload: LogIn, db: Session = Depends(get_db)):
    if not payload.confirmed:
        raise HTTPException(422, "Cần xác nhận món và khẩu phần trước khi lưu")
    food = db.get(Food, payload.food_id)
    if not food:
        raise HTTPException(404, "Food ID không tồn tại")
    record = FoodLog(food_id=food.id, grams=payload.grams, meal_type=payload.meal_type,
                     eaten_at=payload.eaten_at or datetime.now(timezone.utc))
    db.add(record)
    db.commit()
    db.refresh(record)
    return {"id": record.id, "food_id": food.id, "name": food.name, "grams": record.grams,
            "nutrition": nutrition(food, record.grams), "source_reference": food.source_reference,
            "is_verified": food.is_verified}


@app.get("/api/dashboard")
def dashboard(day: date = Query(default_factory=date.today), db: Session = Depends(get_db)):
    logs = db.scalars(select(FoodLog).options(selectinload(FoodLog.food))).all()
    entries = []
    totals = {key: 0.0 for key in ("kcal", "protein", "carb", "fat")}
    for log in logs:
        if log.eaten_at.date() != day:
            continue
        values = nutrition(log.food, log.grams)
        entries.append({"id": log.id, "food_id": log.food_id, "name": log.food.name,
                        "grams": log.grams, "meal_type": log.meal_type, "nutrition": values,
                        "source_reference": log.food.source_reference, "is_verified": log.food.is_verified})
        for key, value in values.items():
            totals[key] += value
    return {"date": day.isoformat(), "totals": {k: round(v, 1) for k, v in totals.items()}, "entries": entries}


class PlanIn(BaseModel):
    week_start: date
    target_kcal: float = Field(ge=900, le=5000)
    avoid_tags: list[str] = []


def plan_data(plan):
    days = []
    for day in range(1, 8):
        items = [i for i in plan.items if i.day == day]
        meals = [{"meal_slot": i.meal_slot, "food_id": i.food_id, "name": i.food.name,
                  "grams": i.grams, "nutrition": nutrition(i.food, i.grams),
                  "source_reference": i.food.source_reference, "is_verified": i.food.is_verified}
                 for i in items]
        days.append({"day": day, "meals": meals,
                     "total_kcal": round(sum(i["nutrition"]["kcal"] for i in meals), 1)})
    return {"id": plan.id, "week_start": plan.week_start, "target_kcal": plan.target_kcal,
            "generation_mode": plan.generation_mode, "model_version": plan.model_version, "days": days}


@app.post("/api/meal-plans/generate", status_code=201)
def create_plan(payload: PlanIn, db: Session = Depends(get_db)):
    records = db.scalars(select(Food)).all()
    allowed = [f for f in records if not (set(f.avoid_tags or []) & set(payload.avoid_tags))]
    if len(allowed) < 3:
        raise HTTPException(422, "Không đủ món phù hợp; cần tối thiểu ba món")
    mode = "gemini"
    model = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
    started = perf_counter()
    try:
        proposed = ai.generate_plan(allowed, payload.target_kcal)
        checked = validate_plan(proposed, [f.id for f in allowed], records, payload.avoid_tags, payload.target_kcal)
        run_status = "ok"
    except Exception:
        mode = "rule_fallback"
        run_status = "fallback"
        model = "deterministic-v1"
        try:
            proposed = fallback_plan(allowed, payload.target_kcal)
            checked = validate_plan(proposed, [f.id for f in allowed], records, payload.avoid_tags, payload.target_kcal)
        except ValueError as exc:
            raise HTTPException(422, str(exc))
    db.add(AiRun(purpose="planner", prompt_version=ai.PLAN_PROMPT_VERSION,
                 model_id=os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite"),
                 latency_ms=round((perf_counter() - started) * 1000), status=run_status))
    plan = MealPlan(week_start=payload.week_start.isoformat(), target_kcal=payload.target_kcal,
                    avoid_tags=payload.avoid_tags, generation_mode=mode, model_version=model)
    for day in checked:
        for meal in day["meals"]:
            plan.items.append(MealPlanItem(day=day["day"], meal_slot=meal["meal_slot"],
                                           food_id=meal["food_id"], grams=meal["grams"]))
    db.add(plan)
    db.commit()
    loaded = db.scalar(select(MealPlan).where(MealPlan.id == plan.id).options(selectinload(MealPlan.items).selectinload(MealPlanItem.food)))
    return plan_data(loaded)


@app.get("/api/meal-plans/{plan_id}")
def get_plan(plan_id: int, db: Session = Depends(get_db)):
    plan = db.scalar(select(MealPlan).where(MealPlan.id == plan_id).options(selectinload(MealPlan.items).selectinload(MealPlanItem.food)))
    if not plan:
        raise HTTPException(404, "Không tìm thấy thực đơn")
    return plan_data(plan)
