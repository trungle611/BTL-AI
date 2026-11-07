from datetime import date


ACTIVITY_FACTORS = {"sedentary": 1.2, "light": 1.375, "moderate": 1.55, "high": 1.725}


def daily_targets(profile, guidance, today: date | None = None):
    """A rough adult planning estimate, never a guarantee of weight change."""
    if not guidance or not all((profile.age, profile.height_cm, profile.weight_kg,
                                profile.sex, profile.activity_level,
                                guidance.target_weight_kg, guidance.target_date)):
        return None
    today = today or date.today()
    deadline = date.fromisoformat(guidance.target_date)
    days = (deadline - today).days
    if days <= 0:
        return None

    weight = profile.weight_kg
    delta = guidance.target_weight_kg - weight
    bmr = 10 * weight + 6.25 * profile.height_cm - 5 * profile.age + (5 if profile.sex == "male" else -161)
    maintenance = bmr * ACTIVITY_FACTORS[profile.activity_level]
    # 7700 kcal/kg is only a short-term planning approximation; adaptation varies.
    requested_adjustment = delta * 7700 / days
    adjustment = max(-500, min(500, requested_adjustment))
    minimum = 1500 if profile.sex == "male" else 1200
    kcal = max(minimum, maintenance + adjustment)
    kcal = round(kcal / 25) * 25
    protein_factor = 1.6 if profile.protein_mode == "strength" else 1.2
    protein = round(weight * protein_factor / 5) * 5
    rate = abs(delta) * 7 / days
    too_fast = (delta < 0 and rate > 0.9) or (delta > 0 and rate > 0.5)
    limited = abs(requested_adjustment) > 500 or (delta < 0 and maintenance + adjustment < minimum)
    return {"kcal": int(kcal), "protein_g": int(protein), "protein_factor": protein_factor,
            "days_remaining": days,
            "target_date": guidance.target_date, "estimated_maintenance_kcal": round(maintenance),
            "timeline_warning": bool(too_fast or limited)}
