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
    catalog = [{"food_id": f.id, "name": f.name, "kcal_100g": f.kcal_100g} for f in foods]
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
