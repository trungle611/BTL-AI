import re
import unicodedata
from difflib import SequenceMatcher


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFD", text.casefold())
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    text = text.replace("đ", "d")
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", text)).strip()


def match_foods(labels, foods, limit=3):
    found = {}
    for rank, label in enumerate(labels):
        query = normalize(label)
        if not query:
            continue
        for food in foods:
            names = [getattr(food, "display_name", None) or food.name] + [alias.alias for alias in food.aliases]
            score = max((1.0 if normalize(name) == query else SequenceMatcher(None, query, normalize(name)).ratio()) for name in names)
            if score >= 0.74:
                current = found.get(food.id)
                value = score - rank * 0.01
                if current is None or value > current[0]:
                    found[food.id] = (value, food)
    return [item[1] for item in sorted(found.values(), key=lambda x: x[0], reverse=True)[:limit]]


def nutrition(food, grams):
    if grams <= 0 or grams > 2000:
        raise ValueError("Khẩu phần phải lớn hơn 0 và không quá 2000 g")
    factor = grams / 100
    return {key: round(getattr(food, key + "_100g") * factor, 1) for key in ("kcal", "protein", "carb", "fat")}


SLOTS = ("breakfast", "lunch", "dinner")


def validate_plan(days, allowed_ids, foods, avoid_tags, target_kcal):
    if len(days) != 7:
        raise ValueError("Thực đơn phải có đúng 7 ngày")
    allowed = set(allowed_ids)
    lookup = {food.id: food for food in foods}
    forbidden = set(avoid_tags)
    result = []
    for expected_day, day in enumerate(days, 1):
        if day.get("day") != expected_day:
            raise ValueError("Ngày trong kế hoạch không hợp lệ")
        meals = day.get("meals", [])
        if len(meals) != 3 or {meal.get("meal_slot") for meal in meals} != set(SLOTS):
            raise ValueError("Mỗi ngày cần ba bữa đúng cấu trúc")
        total = 0.0
        checked = []
        for meal in meals:
            food_id = meal.get("food_id")
            grams = meal.get("grams")
            if food_id not in allowed or food_id not in lookup:
                raise ValueError("Food ID nằm ngoài danh mục được phép")
            food = lookup[food_id]
            if set(food.avoid_tags or []) & forbidden:
                raise ValueError("Món có thành phần cần tránh")
            if not isinstance(grams, (int, float)) or isinstance(grams, bool):
                raise ValueError("Khối lượng không hợp lệ")
            values = nutrition(food, grams)
            total += values["kcal"]
            checked.append({**meal, "name": food.name, "nutrition": values})
        if not 0.8 * target_kcal <= total <= 1.2 * target_kcal:
            raise ValueError("Tổng năng lượng ngoài khoảng mục tiêu")
        result.append({"day": expected_day, "meals": checked, "total_kcal": round(total, 1)})
    return result


def fallback_plan(foods, target_kcal):
    if len(foods) < 3:
        raise ValueError("Cần tối thiểu 3 món đủ điều kiện")
    days = []
    for day in range(1, 8):
        meals = []
        for index, slot in enumerate(SLOTS):
            food = foods[(day - 1 + index) % len(foods)]
            grams = round((target_kcal / 3) / food.kcal_100g * 100)
            if not 1 <= grams <= 2000:
                raise ValueError("Danh mục không đáp ứng mục tiêu năng lượng")
            meals.append({"meal_slot": slot, "food_id": food.id, "grams": grams})
        days.append({"day": day, "meals": meals})
    return days

