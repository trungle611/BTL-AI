"""Small, explicit training templates for the first release."""

def exercise(code, name, category, minutes, sets, reps, detail):
    return {"code": code, "name": name, "category": category,
            "duration_minutes": minutes, "sets": sets, "reps": reps, "detail": detail}


WARMUP = exercise("warmup", "Khởi động", "Chuẩn bị", 8, None, None,
                  "Vận động nhẹ và xoay khớp trong biên độ thoải mái.")
PUSH = [exercise("chest_press", "Đẩy ngực", "Push", 15, 3, "8–12", "Giữ vai ổn định; chọn mức tạ kiểm soát được."),
        exercise("shoulder_press", "Đẩy vai", "Push", 12, 3, "8–12", "Đẩy tạ có kiểm soát, tránh ưỡn lưng quá mức."),
        exercise("triceps", "Duỗi tay sau", "Push", 10, 3, "10–15", "Giữ khuỷu tay ổn định.")]
PULL = [exercise("row", "Kéo lưng", "Pull", 15, 3, "8–12", "Kéo khuỷu tay về sau và kiểm soát nhịp trả tạ."),
        exercise("pulldown", "Kéo xô", "Pull", 12, 3, "8–12", "Giữ thân người ổn định, kéo về phía ngực trên."),
        exercise("biceps", "Cuốn tay trước", "Pull", 10, 3, "10–15", "Không đung đưa thân người.")]
LEGS = [exercise("squat", "Squat", "Legs", 15, 3, "8–12", "Hạ người trong biên độ thoải mái, giữ bàn chân vững."),
        exercise("hinge", "Romanian deadlift", "Legs", 15, 3, "8–12", "Gập tại hông, giữ lưng trung lập và tạ gần chân."),
        exercise("calf", "Nâng bắp chân", "Legs", 8, 3, "12–15", "Lên xuống chậm, không bật nảy.")]
UPPER = [PUSH[0], PULL[0], PUSH[1], PULL[1]]
LOWER = [LEGS[0], LEGS[1], exercise("plank", "Plank", "Core", 8, 3, "20–40 giây", "Giữ thân người thẳng và thở đều.")]
CARDIO = exercise("cardio", "Đi bộ nhanh hoặc đạp xe", "Cardio", 20, None, None,
                  "Giữ nhịp độ có thể nói chuyện; điều chỉnh theo thể lực.")

PLANS = [
    {"id": "gain_ppl", "goal": "gain", "method": "PPL", "name": "PPL · Tăng cơ", "days_per_week": 6,
     "description": "Push, Pull, Legs lặp lại hai vòng mỗi tuần; ưu tiên tăng dần mức tập.",
     "schedule": ["Push", "Pull", "Legs", "Push", "Pull", "Legs", "Nghỉ"],
     "sessions": [PUSH, PULL, LEGS, PUSH, PULL, LEGS, []]},
    {"id": "gain_ul", "goal": "gain", "method": "UL", "name": "Upper/Lower · Tăng cơ", "days_per_week": 4,
     "description": "Bốn buổi thân trên, thân dưới; có ngày nghỉ xen kẽ để hồi phục.",
     "schedule": ["Upper", "Lower", "Nghỉ", "Upper", "Lower", "Nghỉ", "Nghỉ"],
     "sessions": [UPPER, LOWER, [], UPPER, LOWER, [], []]},
    {"id": "lose_ppl", "goal": "lose", "method": "PPL", "name": "PPL · Giảm cân", "days_per_week": 5,
     "description": "Tập kháng lực theo nhóm cơ, kết hợp vận động tim mạch vừa sức.",
     "schedule": ["Push", "Pull", "Legs", "Cardio", "Push/Pull", "Nghỉ", "Nghỉ"],
     "sessions": [PUSH+[CARDIO], PULL+[CARDIO], LEGS, [CARDIO], [PUSH[0], PULL[0], CARDIO], [], []]},
    {"id": "lose_ul", "goal": "lose", "method": "UL", "name": "Upper/Lower · Giảm cân", "days_per_week": 4,
     "description": "Bốn buổi kháng lực thân trên, thân dưới; thêm cardio nhẹ theo sức.",
     "schedule": ["Upper", "Lower", "Nghỉ", "Upper", "Lower", "Nghỉ", "Nghỉ"],
     "sessions": [UPPER+[CARDIO], LOWER, [], UPPER+[CARDIO], LOWER, [], []]},
]


def public_plan(plan):
    return {key: value for key, value in plan.items() if key != "sessions"}


def today_items(plan, weekday):
    session = plan["sessions"][weekday]
    return [{**item, "id": f'{plan["id"]}-{weekday}-{index}-{item["code"]}'}
            for index, item in enumerate(([WARMUP] + session) if session else [])]
