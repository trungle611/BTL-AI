import os
import uuid
import hashlib
import json
from time import perf_counter
from contextlib import asynccontextmanager
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from io import BytesIO
from PIL import Image, UnidentifiedImageError
from fastapi import Depends, FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload
from . import ai
from .core import fallback_plan, match_foods, normalize, nutrition, validate_plan
from .db import Base, engine, get_db, migrate_demo_columns
from .goals import daily_targets
from .models import AiRun, BatchSubmission, Food, FoodAlias, FoodLog, MealPlan, MealPlanItem, Profile, ProfileGuidance, WorkoutProgress, WorkoutSelection, WorkoutVisit
from .workout_plans import PLANS, public_plan, session_items

LOCAL_TZ = ZoneInfo("Asia/Ho_Chi_Minh")
GOAL_ANALYSIS_VERSION = "macro-targets-v1"


def local_today():
    return datetime.now(LOCAL_TZ).date()


def local_date(value):
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(LOCAL_TZ).date()

@asynccontextmanager
async def lifespan(app):
    Base.metadata.create_all(engine)
    migrate_demo_columns()
    if os.getenv("SEED_DEMO") == "1":
        from .seed_demo import seed
        seed()
    yield


app = FastAPI(title="HBTNFIT API", version="0.1.0", lifespan=lifespan)
LOCAL_ORIGINS = [f"http://{host}:{port}" for host in ("localhost", "127.0.0.1") for port in (5173, 5174, 5175)]
PUBLIC_ORIGINS = [origin.strip() for origin in os.getenv("FRONTEND_ORIGINS", "").split(",") if origin.strip()]
app.add_middleware(CORSMiddleware, allow_origins=LOCAL_ORIGINS + PUBLIC_ORIGINS,
                   allow_origin_regex=r"https://[a-z0-9-]+\.vercel\.app" if os.getenv("ALLOW_VERCEL_PREVIEWS") == "1" else None,
                   allow_methods=["*"], allow_headers=["*"])


def visitor(db):
    return db.info["visitor_id"]


def scoped_key(db, value):
    return hashlib.sha1(f"{visitor(db)}:{value}".encode()).hexdigest()


def visible_food(food, db):
    return food is not None and (food.owner_id is None or food.owner_id == visitor(db))


def profile_record(db):
    return db.scalar(select(Profile).where(Profile.visitor_id == visitor(db)))


def guidance_record(db):
    return db.scalar(select(ProfileGuidance).where(ProfileGuidance.visitor_id == visitor(db)))


def selection_record(db):
    return db.scalar(select(WorkoutSelection).where(WorkoutSelection.visitor_id == visitor(db)))


def food_data(food):
    return {"id": food.id, "name": food.display_name or food.name, "kcal_100g": food.kcal_100g,
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
    target_weight_kg: float | None = Field(default=None, ge=25, le=400)
    target_date: date | None = None
    sex: str | None = Field(default=None, pattern="^(female|male)$")
    activity_level: str | None = Field(default=None, pattern="^(sedentary|light|moderate|high)$")
    protein_mode: str = Field(default="balanced", pattern="^(balanced|strength)$")
    goal: str = Field(default="maintain", pattern="^(maintain|gain|lose)$")
    avoid_tags: list[str] = []
    target_kcal: float = Field(default=1800, ge=900, le=5000)


def profile_data(profile, guidance=None):
    analysis = guidance.analysis if guidance and guidance.analysis and guidance.analysis.get("target_version") == GOAL_ANALYSIS_VERSION else None
    return {"age": profile.age, "height_cm": profile.height_cm,
            "weight_kg": profile.weight_kg, "sex": profile.sex,
            "activity_level": profile.activity_level, "protein_mode": profile.protein_mode or "balanced", "goal": profile.goal,
            "avoid_tags": profile.avoid_tags or [], "target_kcal": profile.target_kcal,
            "target_weight_kg": guidance.target_weight_kg if guidance else None,
            "target_date": guidance.target_date if guidance else None,
            "daily_targets": daily_targets(profile, guidance, local_today()),
            "analysis": analysis,
            "food_choice": guidance.food_choice if analysis else None,
            "workout_choice": guidance.workout_choice if analysis else None}


@app.get("/api/profile")
def get_profile(db: Session = Depends(get_db)):
    profile = profile_record(db)
    return profile_data(profile, guidance_record(db)) if profile else ProfileIn().model_dump(mode="json") | {"daily_targets":None,"analysis":None,"food_choice":None,"workout_choice":None}


@app.put("/api/profile")
def save_profile(payload: ProfileIn, db: Session = Depends(get_db)):
    if payload.target_date and payload.target_date <= local_today():
        raise HTTPException(422, "Ngày hoàn thành mục tiêu phải sau hôm nay")
    profile = profile_record(db) or Profile(visitor_id=visitor(db))
    guidance = guidance_record(db) or ProfileGuidance(visitor_id=visitor(db))
    if (profile.weight_kg != payload.weight_kg or guidance.target_weight_kg != payload.target_weight_kg
            or guidance.target_date != (payload.target_date.isoformat() if payload.target_date else None)
            or profile.avoid_tags != payload.avoid_tags or profile.age != payload.age
            or profile.height_cm != payload.height_cm or profile.goal != payload.goal
            or profile.sex != payload.sex or profile.activity_level != payload.activity_level
            or (profile.protein_mode or "balanced") != payload.protein_mode
            or (guidance.analysis and guidance.analysis.get("target_version") != GOAL_ANALYSIS_VERSION)):
        guidance.analysis = None
        guidance.food_choice = None
        guidance.workout_choice = None
    guidance.target_weight_kg = payload.target_weight_kg
    guidance.target_date = payload.target_date.isoformat() if payload.target_date else None
    for key, value in payload.model_dump(exclude={"target_weight_kg", "target_date"}).items():
        setattr(profile, key, value)
    db.add(profile)
    db.add(guidance)
    db.commit()
    return profile_data(profile, guidance)


@app.post("/api/profile/analyze")
def analyze_profile(db: Session = Depends(get_db)):
    profile = profile_record(db)
    guidance = guidance_record(db)
    if not profile or not guidance or profile.weight_kg is None or guidance.target_weight_kg is None:
        raise HTTPException(422, "Hãy lưu cân nặng hiện tại và cân nặng mong muốn trước")
    goal = "gain" if guidance.target_weight_kg > profile.weight_kg + 0.5 else "lose" if guidance.target_weight_kg < profile.weight_kg - 0.5 else (profile.goal if profile.goal != "maintain" else "gain")
    options = [plan for plan in PLANS if plan["goal"] == goal]
    started = perf_counter()
    try:
        generated = ai.generate_profile_guidance(profile, guidance.target_weight_kg, [plan["name"] for plan in options],
                                                 daily_targets(profile, guidance, local_today()))
        food_options = generated.get("food_options", [])[:2]
        if len(food_options) != 2 or any(not item.get("title") or not item.get("detail") for item in food_options):
            raise ValueError("AI chưa trả đủ phương án")
        analysis = {"target_version": GOAL_ANALYSIS_VERSION, "summary": generated["summary"][:700],
                    "food_options": [{"id": f"food_{index+1}", "title": item["title"][:100],
                                      "detail": item["detail"][:500], "examples": item.get("examples", [])[:4]}
                                     for index, item in enumerate(food_options)],
                    "workout_options": [{"id": plan["id"], "name": plan["name"],
                                         "detail": generated["ppl_note" if plan["method"] == "PPL" else "ul_note"][:500]}
                                        for plan in options],
                    "model": os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")}
        status = "ok"
    except Exception as exc:
        status = "error"
        raise HTTPException(503, "Chưa tạo được phân tích AI. Hãy thử lại sau") from exc
    finally:
        db.add(AiRun(purpose="profile", prompt_version=ai.GUIDANCE_PROMPT_VERSION,
                     model_id=os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite"),
                     latency_ms=round((perf_counter()-started)*1000), status=status))
        db.commit()
    guidance.analysis = analysis
    guidance.food_choice = None
    guidance.workout_choice = None
    db.commit()
    return profile_data(profile, guidance)


class GuidanceChoiceIn(BaseModel):
    food_choice: str | None = None
    workout_choice: str | None = None


@app.post("/api/profile/choice")
def choose_guidance(payload: GuidanceChoiceIn, db: Session = Depends(get_db)):
    guidance = guidance_record(db)
    profile = profile_record(db)
    if not profile or not guidance or not guidance.analysis:
        raise HTTPException(409, "Hãy tạo phân tích AI trước")
    if not payload.food_choice and not payload.workout_choice:
        raise HTTPException(422, "Hãy chọn một phương án")
    if payload.food_choice:
        if payload.food_choice not in {item["id"] for item in guidance.analysis["food_options"]}:
            raise HTTPException(422, "Phương án ăn uống không hợp lệ")
        guidance.food_choice = payload.food_choice
    if payload.workout_choice:
        if payload.workout_choice not in {item["id"] for item in guidance.analysis["workout_options"]}:
            raise HTTPException(422, "Giáo án không hợp lệ")
        guidance.workout_choice = payload.workout_choice
        selection = selection_record(db) or WorkoutSelection(visitor_id=visitor(db), plan_id=payload.workout_choice)
        selection.plan_id = payload.workout_choice
        db.add(selection)
    db.commit()
    return profile_data(profile, guidance)


@app.get("/api/foods")
def foods(q: str = "", db: Session = Depends(get_db)):
    records = db.scalars(select(Food).where((Food.owner_id.is_(None)) | (Food.owner_id == visitor(db))).options(selectinload(Food.aliases))).all()
    if q:
        query = normalize(q)
        records = [f for f in records if any(query in normalize(n) for n in [f.display_name or f.name] + [a.alias for a in f.aliases])]
    return [food_data(f) for f in records[:200]]


@app.get("/api/foods/{food_id}")
def get_food(food_id: str, db: Session = Depends(get_db)):
    food = db.scalar(select(Food).where(Food.id == food_id).options(selectinload(Food.aliases)))
    if not visible_food(food, db):
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
    records = db.scalars(select(Food).where((Food.owner_id.is_(None)) | (Food.owner_id == visitor(db))).options(selectinload(Food.aliases))).all()
    dishes = []
    for item in result.get("dishes", [])[:5]:
        labels = [label for label in item.get("candidate_labels", [])[:3] if isinstance(label, str)]
        candidates = match_foods(labels, records)
        raw_estimate = item.get("estimated_nutrition_100g") or {}
        estimate = None
        try:
            values = {key: float(raw_estimate[key]) for key in ("kcal", "protein", "carb", "fat")}
            if 0 < values["kcal"] <= 900 and all(0 <= values[key] <= 100 for key in ("protein", "carb", "fat")):
                estimate = {key: round(value, 1) for key, value in values.items()}
        except (KeyError, TypeError, ValueError):
            pass
        dishes.append({"suggested_labels": labels, "candidates": [food_data(f) for f in candidates],
                       "estimated_nutrition_100g": estimate,
                       "visible_ingredients": item.get("visible_ingredients", []),
                       "uncertainty_reason": item.get("uncertainty_reason", "")})
    if not dishes:
        dishes = [{"suggested_labels": [], "candidates": [], "visible_ingredients": [],
                   "uncertainty_reason": result.get("warning") or "Không nhận diện được món ăn"}]
    return {"request_id": request_id, "status": "needs_confirmation" if any(d["candidates"] for d in dishes) else "unknown",
            "dishes": dishes, "warnings": [result["warning"]] if result.get("warning") else [],
            "prompt_version": ai.SCAN_PROMPT_VERSION}


class LogIn(BaseModel):
    food_id: str | None = None
    custom_food: "CustomFoodIn | None" = None
    grams: float = Field(gt=0, le=2000)
    meal_type: str = Field(pattern="^(breakfast|lunch|dinner|snack)$")
    eaten_at: datetime | None = None
    confirmed: bool


class CustomFoodIn(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    kcal_100g: float = Field(default=0, ge=0, le=900)
    protein_100g: float = Field(default=0, ge=0, le=100)
    carb_100g: float = Field(default=0, ge=0, le=100)
    fat_100g: float = Field(default=0, ge=0, le=100)


LogIn.model_rebuild()


class BatchLogIn(BaseModel):
    items: list[LogIn] = Field(min_length=1, max_length=5)
    confirmation_id: str | None = Field(default=None, min_length=8, max_length=80)


def log_response(log, food):
    return {"id": log.id, "food_id": food.id, "name": food.display_name or food.name,
            "grams": log.grams, "nutrition": nutrition(food, log.grams),
            "source_reference": food.source_reference, "is_verified": food.is_verified}


@app.post("/api/food-logs/batch", status_code=201)
def add_logs_batch(payload: BatchLogIn, db: Session = Depends(get_db)):
    request_hash = hashlib.sha256(json.dumps([item.model_dump(mode="json") for item in payload.items],
                                            ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()
    submission_key = scoped_key(db, payload.confirmation_id) if payload.confirmation_id else None
    if submission_key:
        prior = db.get(BatchSubmission, submission_key)
        if prior:
            if prior.request_hash != request_hash:
                raise HTTPException(409, "Mã xác nhận đã dùng với nội dung khác")
            logs = [db.get(FoodLog, log_id) for log_id in prior.log_ids]
            return {"entries": [log_response(log, db.get(Food, log.food_id)) for log in logs if log and log.visitor_id == visitor(db)]}
    records = []
    for item in payload.items:
        if not item.confirmed:
            raise HTTPException(422, "Cần xác nhận từng món và khẩu phần trước khi lưu")
        if bool(item.food_id) == bool(item.custom_food):
            raise HTTPException(422, "Chọn món trong danh mục hoặc nhập một món mới")
        food = db.get(Food, item.food_id) if item.food_id else None
        if item.food_id and not visible_food(food, db):
            raise HTTPException(404, f"Food ID không tồn tại: {item.food_id}")
        records.append((item, food))
    created = []
    for item, food in records:
        if item.custom_food:
            custom = item.custom_food
            name = custom.name.strip()
            if len(name) < 2:
                raise HTTPException(422, "Tên món phải có ít nhất 2 ký tự")
            food = db.scalar(select(Food).where(Food.owner_id == visitor(db), Food.display_name == name))
            catalog_food = db.scalar(select(Food).where(Food.owner_id.is_(None), Food.name == name))
            if catalog_food:
                raise HTTPException(409, "Tên món đã có trong danh mục; hãy chọn món có sẵn")
            if food and food.source_type != "user_entered":
                raise HTTPException(409, "Tên món đã có trong danh mục; hãy chọn món có sẵn")
            if food and food.kcal_100g == 0 and custom.kcal_100g > 0:
                food.kcal_100g = custom.kcal_100g
                food.protein_100g = custom.protein_100g
                food.carb_100g = custom.carb_100g
                food.fat_100g = custom.fat_100g
                food.source_reference = "Người dùng tự nhập/điều chỉnh ước tính; chưa kiểm chứng"
            if not food:
                food = Food(id=f"user-{uuid.uuid4().hex[:32]}", name=f"{name[:130]} [{uuid.uuid4().hex[:12]}]",
                            display_name=name, owner_id=visitor(db),
                            kcal_100g=custom.kcal_100g, protein_100g=custom.protein_100g,
                            carb_100g=custom.carb_100g, fat_100g=custom.fat_100g,
                            source_type="user_entered", source_reference="Người dùng tự nhập; chưa kiểm chứng",
                            reference_mass_g=100, data_version="user-v1", is_verified=False, avoid_tags=[])
                db.add(food)
                db.flush()
        log = FoodLog(food_id=food.id, visitor_id=visitor(db), grams=item.grams, meal_type=item.meal_type,
                      eaten_at=item.eaten_at or datetime.now(timezone.utc))
        db.add(log)
        created.append((log, food))
    db.flush()
    if submission_key:
        db.add(BatchSubmission(confirmation_id=submission_key,
                               request_hash=request_hash, log_ids=[log.id for log, _ in created]))
    db.commit()
    return {"entries": [log_response(log, food) for log, food in created]}


@app.post("/api/food-logs", status_code=201)
def add_log(payload: LogIn, db: Session = Depends(get_db)):
    if not payload.confirmed:
        raise HTTPException(422, "Cần xác nhận món và khẩu phần trước khi lưu")
    food = db.get(Food, payload.food_id)
    if not visible_food(food, db):
        raise HTTPException(404, "Food ID không tồn tại")
    record = FoodLog(food_id=food.id, visitor_id=visitor(db), grams=payload.grams, meal_type=payload.meal_type,
                     eaten_at=payload.eaten_at or datetime.now(timezone.utc))
    db.add(record)
    db.commit()
    db.refresh(record)
    return {"id": record.id, "food_id": food.id, "name": food.display_name or food.name, "grams": record.grams,
            "nutrition": nutrition(food, record.grams), "source_reference": food.source_reference,
            "is_verified": food.is_verified}


class LogUpdate(BaseModel):
    grams: float = Field(gt=0, le=2000)
    meal_type: str = Field(pattern="^(breakfast|lunch|dinner|snack)$")


@app.patch("/api/food-logs/{log_id}")
def update_log(log_id: int, payload: LogUpdate, db: Session = Depends(get_db)):
    log = db.get(FoodLog, log_id)
    if not log or log.visitor_id != visitor(db):
        raise HTTPException(404, "Không tìm thấy món trong nhật ký")
    log.grams = payload.grams
    log.meal_type = payload.meal_type
    db.commit()
    db.refresh(log)
    food = db.get(Food, log.food_id)
    return {"id": log.id, "food_id": food.id, "name": food.display_name or food.name, "grams": log.grams,
            "meal_type": log.meal_type, "nutrition": nutrition(food, log.grams),
            "source_reference": food.source_reference, "is_verified": food.is_verified}


@app.delete("/api/food-logs/{log_id}", status_code=204)
def delete_log(log_id: int, db: Session = Depends(get_db)):
    log = db.get(FoodLog, log_id)
    if not log or log.visitor_id != visitor(db):
        raise HTTPException(404, "Không tìm thấy món trong nhật ký")
    db.delete(log)
    db.commit()


@app.get("/api/dashboard")
def dashboard(day: date = Query(default_factory=local_today), db: Session = Depends(get_db)):
    logs = db.scalars(select(FoodLog).where(FoodLog.visitor_id == visitor(db)).options(selectinload(FoodLog.food))).all()
    entries = []
    totals = {key: 0.0 for key in ("kcal", "protein", "carb", "fat")}
    for log in logs:
        if local_date(log.eaten_at) != day:
            continue
        values = nutrition(log.food, log.grams)
        entries.append({"id": log.id, "food_id": log.food_id, "name": log.food.display_name or log.food.name,
                        "grams": log.grams, "meal_type": log.meal_type, "nutrition": values,
                        "source_reference": log.food.source_reference, "is_verified": log.food.is_verified})
        for key, value in values.items():
            totals[key] += value
    return {"date": day.isoformat(), "totals": {k: round(v, 1) for k, v in totals.items()}, "entries": entries}


WORKOUTS = [
    {"id": "warmup", "name": "Khởi động toàn thân", "category": "Khởi động", "duration_minutes": 8,
     "sets": None, "reps": None, "detail": "Đi bộ tại chỗ, xoay khớp nhẹ và tăng dần nhịp vận động theo khả năng."},
    {"id": "squat", "name": "Squat cơ bản", "category": "Thân dưới", "duration_minutes": 12,
     "sets": 3, "reps": 10, "detail": "Đứng chân rộng bằng vai, hạ người trong phạm vi thoải mái rồi đứng lên. Dừng nếu đau."},
    {"id": "plank", "name": "Plank", "category": "Cơ trung tâm", "duration_minutes": 8,
     "sets": 3, "reps": "20–30 giây", "detail": "Giữ thân người thẳng và thở đều; nghỉ giữa các hiệp khi cần."},
]


def workout_data(db, day):
    selection = selection_record(db)
    plan = next((plan for plan in PLANS if selection and plan["id"] == selection.plan_id), None)
    visits = db.scalars(select(WorkoutVisit).where(WorkoutVisit.plan_id == scoped_key(db, plan["id"]))).all() if plan else []
    today_visit = next((visit for visit in visits if visit.day == day.isoformat()), None)
    completed_sessions = sum(visit.status == "completed" and visit.day <= day.isoformat() for visit in visits)
    session_index = (today_visit.session_index if today_visit else completed_sessions % len(plan["sessions"])) if plan else None
    items = session_items(plan, session_index) if plan else WORKOUTS
    progress = {row.workout_id: row for row in db.scalars(select(WorkoutProgress).where(WorkoutProgress.day == day.isoformat()))}
    return {"date": day.isoformat(), "selected_plan": public_plan(plan) if plan else None,
            "session_name": plan["schedule"][session_index] if plan else "Làm quen",
            "session_number": session_index + 1 if plan else None,
            "attendance": today_visit.status if today_visit else None,
            "attendance_history": [{"day": (day - timedelta(days=offset)).isoformat(),
                                    "status": next((v.status for v in visits if v.day == (day - timedelta(days=offset)).isoformat()), None)}
                                   for offset in range(6, -1, -1)] if plan else [],
            "items": [{**workout, "status": progress[scoped_key(db, workout["id"])].status if scoped_key(db, workout["id"]) in progress else "not_started"}
            for workout in items]}


@app.get("/api/workouts/plans")
def workout_plans():
    return [public_plan(plan) for plan in PLANS]


class WorkoutSelectIn(BaseModel):
    plan_id: str


@app.post("/api/workouts/select")
def select_workout_plan(payload: WorkoutSelectIn, db: Session = Depends(get_db)):
    if payload.plan_id not in {plan["id"] for plan in PLANS}:
        raise HTTPException(404, "Không tìm thấy giáo án")
    selection = selection_record(db) or WorkoutSelection(visitor_id=visitor(db), plan_id=payload.plan_id)
    selection.plan_id = payload.plan_id
    db.add(selection)
    db.commit()
    return workout_data(db, local_today())


@app.get("/api/workouts/today")
def workouts_today(db: Session = Depends(get_db)):
    return workout_data(db, local_today())


class AttendanceIn(BaseModel):
    status: str = Field(pattern="^(attended|missed)$")


@app.post("/api/workouts/attendance")
def record_attendance(payload: AttendanceIn, db: Session = Depends(get_db)):
    selection = selection_record(db)
    if not selection:
        raise HTTPException(409, "Hãy chọn giáo án trước")
    data = workout_data(db, local_today())
    today = local_today().isoformat()
    visit = db.scalar(select(WorkoutVisit).where(WorkoutVisit.plan_id == scoped_key(db, selection.plan_id), WorkoutVisit.day == today))
    if visit and visit.status == "completed":
        raise HTTPException(409, "Buổi tập đã hoàn thành")
    if not visit:
        visit = WorkoutVisit(plan_id=scoped_key(db, selection.plan_id), day=today,
                             session_index=data["session_number"] - 1, status=payload.status)
        db.add(visit)
    else:
        visit.status = payload.status
    db.commit()
    return workout_data(db, local_today())


@app.post("/api/workouts/{workout_id}/{action}")
def workout_action(workout_id: str, action: str, db: Session = Depends(get_db)):
    data = workout_data(db, local_today())
    if workout_id not in {item["id"] for item in data["items"]}:
        raise HTTPException(404, "Không tìm thấy bài tập")
    if action not in {"start", "complete"}:
        raise HTTPException(422, "Thao tác không hợp lệ")
    if data["selected_plan"] and data["attendance"] != "attended":
        raise HTTPException(409, "Hãy ghi nhận có đi tập hôm nay trước")
    today = local_today().isoformat()
    progress = db.scalar(select(WorkoutProgress).where(WorkoutProgress.workout_id == scoped_key(db, workout_id),
                                                       WorkoutProgress.day == today))
    if not progress:
        progress = WorkoutProgress(workout_id=scoped_key(db, workout_id), day=today)
        db.add(progress)
    if action == "start" and progress.status != "completed":
        progress.status = "started"
        progress.started_at = progress.started_at or datetime.now(timezone.utc)
    if action == "complete":
        progress.status = "completed"
        progress.started_at = progress.started_at or datetime.now(timezone.utc)
        progress.completed_at = datetime.now(timezone.utc)
        db.flush()
        if data["selected_plan"]:
            statuses = {row.workout_id: row.status for row in db.scalars(
                select(WorkoutProgress).where(WorkoutProgress.day == today))}
            if all(statuses.get(scoped_key(db, item["id"])) == "completed" for item in data["items"]):
                visit = db.scalar(select(WorkoutVisit).where(
                    WorkoutVisit.plan_id == scoped_key(db, data["selected_plan"]["id"]), WorkoutVisit.day == today))
                visit.status = "completed"
    db.commit()
    return workout_data(db, local_today())


class PlanIn(BaseModel):
    week_start: date
    target_kcal: float = Field(ge=900, le=5000)
    avoid_tags: list[str] = []


def plan_data(plan):
    days = []
    for day in range(1, 8):
        items = [i for i in plan.items if i.day == day]
        meals = [{"meal_slot": i.meal_slot, "food_id": i.food_id, "name": i.food.display_name or i.food.name,
                  "grams": i.grams, "nutrition": nutrition(i.food, i.grams),
                  "source_reference": i.food.source_reference, "is_verified": i.food.is_verified}
                 for i in items]
        days.append({"day": day, "meals": meals,
                     "total_kcal": round(sum(i["nutrition"]["kcal"] for i in meals), 1)})
    return {"id": plan.id, "week_start": plan.week_start, "target_kcal": plan.target_kcal,
            "generation_mode": plan.generation_mode, "model_version": plan.model_version, "days": days}


@app.post("/api/meal-plans/generate", status_code=201)
def create_plan(payload: PlanIn, db: Session = Depends(get_db)):
    records = db.scalars(select(Food).where((Food.owner_id.is_(None)) | (Food.owner_id == visitor(db)))).all()
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
    plan = MealPlan(week_start=payload.week_start.isoformat(), visitor_id=visitor(db), target_kcal=payload.target_kcal,
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
    plan = db.scalar(select(MealPlan).where(MealPlan.id == plan_id, MealPlan.visitor_id == visitor(db)).options(selectinload(MealPlan.items).selectinload(MealPlanItem.food)))
    if not plan:
        raise HTTPException(404, "Không tìm thấy thực đơn")
    return plan_data(plan)
