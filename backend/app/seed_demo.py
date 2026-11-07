from .db import Base, SessionLocal, engine
from .models import Food, FoodAlias


DEMO = [
    ("DEMO_001", "Phở bò", 100, 7, 10, 3, ["beef"], ["phở tái"]),
    ("DEMO_002", "Cơm tấm", 180, 8, 23, 6, ["pork"], ["cơm sườn"]),
    ("DEMO_003", "Bún chả", 145, 8, 16, 5, ["pork"], []),
    ("DEMO_004", "Gỏi cuốn tôm", 110, 6, 14, 3, ["shrimp"], ["gỏi cuốn"]),
]


def seed():
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        for food_id, name, kcal, protein, carb, fat, tags, aliases in DEMO:
            if db.get(Food, food_id):
                continue
            food = Food(id=food_id, name=name, kcal_100g=kcal, protein_100g=protein,
                        carb_100g=carb, fat_100g=fat, source_type="demo_synthetic",
                        source_reference="Dữ liệu tổng hợp để kiểm thử; không dùng làm tư vấn dinh dưỡng",
                        reference_mass_g=100, data_version="demo-v1", is_verified=False,
                        avoid_tags=tags)
            food.aliases = [FoodAlias(alias=a) for a in aliases]
            db.add(food)
        db.commit()


if __name__ == "__main__":
    seed()
    print("Demo foods ready")

