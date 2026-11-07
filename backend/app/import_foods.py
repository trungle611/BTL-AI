import argparse
import csv
from sqlalchemy import select
from .db import Base, SessionLocal, engine
from .models import Food, FoodAlias


REQUIRED = {"id", "name", "kcal_100g", "protein_100g", "carb_100g", "fat_100g",
            "source_type", "source_reference", "data_version", "is_verified", "avoid_tags", "aliases"}


def import_csv(path):
    Base.metadata.create_all(engine)
    with open(path, encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        if not REQUIRED.issubset(reader.fieldnames or []):
            raise ValueError("CSV thiếu cột bắt buộc")
        rows = list(reader)
    with SessionLocal() as db:
        for row in rows:
            if not row["source_reference"].strip():
                raise ValueError(f"{row['id']}: thiếu nguồn")
            numeric = {key: float(row[key]) for key in ("kcal_100g", "protein_100g", "carb_100g", "fat_100g")}
            if any(value < 0 for value in numeric.values()) or numeric["kcal_100g"] <= 0:
                raise ValueError(f"{row['id']}: giá trị dinh dưỡng không hợp lệ")
            if db.get(Food, row["id"]):
                raise ValueError(f"{row['id']}: ID đã tồn tại")
            food = Food(id=row["id"], name=row["name"], **numeric,
                        source_type=row["source_type"], source_reference=row["source_reference"],
                        reference_mass_g=100, data_version=row["data_version"],
                        is_verified=row["is_verified"].lower() == "true",
                        avoid_tags=[s.strip() for s in row["avoid_tags"].split(";") if s.strip()])
            food.aliases = [FoodAlias(alias=s.strip()) for s in row["aliases"].split(";") if s.strip()]
            db.add(food)
        db.commit()
    return len(rows)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("csv_path")
    args = parser.parse_args()
    print(f"Imported {import_csv(args.csv_path)} foods")

