import json
import os
import time
from pathlib import Path
from google import genai
from google.genai import types
from google.genai import errors
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

SCAN_PROMPT_VERSION = "scan-v2-multi-dish"
PLAN_PROMPT_VERSION = "plan-v1"
GUIDANCE_PROMPT_VERSION = "profile-guidance-v3-protein-choice"


def client():
    key = os.getenv("GEMINI_API_KEY")
    return genai.Client(api_key=key, http_options=types.HttpOptions(timeout=20000)) if key else None


def call_with_retry(fn):
    for attempt in range(2):
        try:
            return fn()
        except errors.APIError as exc:
            if attempt or exc.code not in (429, 503):
                raise
            time.sleep(0.5)


def scan_image(image_bytes: bytes, mime_type: str):
    ai = client()
    if ai is None:
        raise RuntimeError("Chưa cấu hình GEMINI_API_KEY")
    prompt = ("Hãy nhận diện từng món ăn riêng biệt nhìn thấy trong ảnh, tối đa 5 món. "
              "Với mỗi món, trả tối đa 3 tên món có thể là gì theo thứ tự khả năng; không gộp các món khác nhau. "
              "Nếu ảnh mờ hoặc không phải đồ ăn thì trả dishes là mảng rỗng và nêu cảnh báo. "
              "Không tự đoán số gam, năng lượng hay macro. Không tạo food_id. "
              "Mọi kết quả đều cần người dùng xác nhận trước khi lưu.")
    dish_schema = {"type": "object", "properties": {
        "candidate_labels": {"type": "array", "items": {"type": "string"}},
        "visible_ingredients": {"type": "array", "items": {"type": "string"}},
        "uncertainty_reason": {"type": "string"}},
        "required": ["candidate_labels", "visible_ingredients", "uncertainty_reason"]}
    schema = {"type": "object", "properties": {
        "dishes": {"type": "array", "items": dish_schema},
        "warning": {"type": "string"}},
        "required": ["dishes", "warning"]}
    response = call_with_retry(lambda: ai.models.generate_content(
        model=os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite"),
        contents=[types.Part.from_bytes(data=image_bytes, mime_type=mime_type), prompt],
        config=types.GenerateContentConfig(response_mime_type="application/json", response_schema=schema),
    ))
    return json.loads(response.text)


def generate_plan(foods, target_kcal):
    ai = client()
    if ai is None:
        raise RuntimeError("Chưa cấu hình GEMINI_API_KEY")
    catalog = [{"food_id": f.id, "name": f.display_name or f.name, "kcal_100g": f.kcal_100g} for f in foods]
    prompt = ("Lập thực đơn đúng 7 ngày, mỗi ngày đúng 3 bữa breakfast, lunch, dinner. "
              "Chỉ dùng food_id trong danh mục. Chọn grams từ 1 đến 2000 để tổng năng lượng mỗi ngày "
              "nằm trong khoảng 80%-120% mục tiêu. Không tự đưa số macro. "
              f"Mục tiêu {target_kcal} kcal/ngày. Danh mục: {json.dumps(catalog, ensure_ascii=False)}")
    schema = {"type": "object", "properties": {"days": {"type": "array", "items": {"type": "object", "properties": {
        "day": {"type": "integer"}, "meals": {"type": "array", "items": {"type": "object", "properties": {
            "meal_slot": {"type": "string"}, "food_id": {"type": "string"}, "grams": {"type": "number"}},
            "required": ["meal_slot", "food_id", "grams"]}}}, "required": ["day", "meals"]}}}, "required": ["days"]}
    response = call_with_retry(lambda: ai.models.generate_content(
        model=os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite"), contents=prompt,
        config=types.GenerateContentConfig(response_mime_type="application/json", response_schema=schema),
    ))
    return json.loads(response.text)["days"]


def generate_profile_guidance(profile, target_weight_kg, plan_names, targets=None):
    ai = client()
    if ai is None:
        raise RuntimeError("Chưa cấu hình GEMINI_API_KEY")
    context = {"age": profile.age, "height_cm": profile.height_cm,
               "current_weight_kg": profile.weight_kg, "target_weight_kg": target_weight_kg,
               "sex_for_estimate": profile.sex, "activity_level": profile.activity_level,
               "daily_targets_estimate": targets,
               "avoid_ingredients": profile.avoid_tags or [], "available_workouts": plan_names}
    prompt = ("Bạn là trợ lý sức khỏe cho người trưởng thành. Đọc dữ liệu hồ sơ dưới đây và trả lời tiếng Việt. "
              "Đưa ra phân tích ngắn, hai cách ăn uống khác nhau với ví dụ món/bữa cụ thể, "
              "và một nhận xét ngắn cho PPL, một cho Upper/Lower để người dùng tự chọn. "
              "Ưu tiên ăn đủ chất và tập kháng lực phù hợp, không đề xuất ăn kiêng cực đoan, "
              "Nếu có daily_targets_estimate, gợi ý món phù hợp với kcal và protein đó nhưng không tự đổi con số; "
              "nếu thiếu, không tự đưa kcal/ngày. Không hứa đạt cân nặng đúng hạn, không chẩn đoán. "
              "Tôn trọng thành phần cần tránh. Nếu mục tiêu có vẻ không phù hợp, nói cần tham khảo chuyên gia. "
              f"Hồ sơ: {json.dumps(context, ensure_ascii=False)}")
    schema = {"type":"object","properties":{
        "summary":{"type":"string"},
        "food_options":{"type":"array","items":{"type":"object","properties":{
            "title":{"type":"string"},"detail":{"type":"string"},
            "examples":{"type":"array","items":{"type":"string"}}},
            "required":["title","detail","examples"]}},
        "ppl_note":{"type":"string"},"ul_note":{"type":"string"}},
        "required":["summary","food_options","ppl_note","ul_note"]}
    response = call_with_retry(lambda: ai.models.generate_content(
        model=os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite"), contents=prompt,
        config=types.GenerateContentConfig(response_mime_type="application/json", response_schema=schema)))
    return json.loads(response.text)
