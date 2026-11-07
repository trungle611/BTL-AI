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

EXERCISE_GUIDE = {
    "warmup": (0, ["Đi bộ hoặc đạp xe rất nhẹ 3–5 phút.", "Xoay vai, hông, gối và cổ chân nhẹ nhàng.", "Làm một hiệp nhẹ của động tác chính trước khi tăng tải."]),
    "chest_press": (90, ["Đặt hai bàn chân vững, ép nhẹ bả vai vào ghế.", "Hạ tạ có kiểm soát về gần ngực, khuỷu tay không xòe ngang hoàn toàn.", "Đẩy lên và thở ra, giữ cổ tay thẳng."]),
    "shoulder_press": (90, ["Ngồi hoặc đứng vững, siết nhẹ cơ bụng.", "Đẩy tạ lên trên trong tầm vận động thoải mái.", "Hạ chậm về ngang vai, tránh ưỡn lưng."]),
    "triceps": (60, ["Giữ khuỷu tay gần thân người.", "Duỗi cẳng tay đến khi tay gần thẳng, không khóa khớp mạnh.", "Trở về chậm và giữ vai ổn định."]),
    "row": (90, ["Giữ lưng trung lập và thân người ổn định.", "Kéo khuỷu tay về phía sau, đưa tay cầm gần thân.", "Thả tạ chậm, không giật lưng."]),
    "pulldown": (90, ["Ngồi vững, giữ ngực mở và vai hạ.", "Kéo thanh về phía ngực trên bằng khuỷu tay.", "Đưa thanh lên chậm, không ngả người quá mức."]),
    "biceps": (60, ["Đứng vững, giữ khuỷu tay gần thân.", "Gập khuỷu để nâng tạ, không vung người.", "Hạ tạ chậm về vị trí đầu."]),
    "squat": (120, ["Đứng chân khoảng rộng vai, bàn chân đặt chắc.", "Hạ hông và gối trong biên độ kiểm soát, giữ lưng trung lập.", "Đẩy chân xuống sàn để đứng lên, tránh gối sụp vào trong."]),
    "hinge": (120, ["Giữ tạ gần đùi, gối hơi chùng.", "Đẩy hông ra sau, hạ tạ dọc chân với lưng trung lập.", "Dùng hông đứng lên, không giật bằng lưng dưới."]),
    "calf": (60, ["Đứng vững và bám điểm tựa nếu cần.", "Nâng gót lên chậm, giữ một nhịp ở trên.", "Hạ gót có kiểm soát."]),
    "plank": (60, ["Chống khuỷu tay dưới vai, duỗi chân ra sau.", "Siết nhẹ bụng và mông, giữ thân người thành một đường thẳng.", "Thở đều; dừng khi không giữ được tư thế."]),
    "cardio": (0, ["Khởi đầu chậm 3–5 phút.", "Đi bộ nhanh hoặc đạp xe ở nhịp có thể nói chuyện.", "Giảm tốc 3–5 phút trước khi dừng."]),
}

PLANS = [
    {"id": "gain_ppl", "goal": "gain", "method": "PPL", "name": "PPL · Tăng cơ",
     "description": "Push, Pull, Legs theo thứ tự; nghỉ khi cần rồi tiếp tục đúng buổi kế tiếp.",
     "schedule": ["Push", "Pull", "Legs", "Push", "Pull", "Legs"],
     "sessions": [PUSH, PULL, LEGS, PUSH, PULL, LEGS]},
    {"id": "gain_ul", "goal": "gain", "method": "UL", "name": "Upper/Lower · Tăng cơ",
     "description": "Luân phiên thân trên và thân dưới; chọn ngày nghỉ phù hợp với lịch cá nhân.",
     "schedule": ["Upper", "Lower", "Upper", "Lower"],
     "sessions": [UPPER, LOWER, UPPER, LOWER]},
    {"id": "lose_ppl", "goal": "lose", "method": "PPL", "name": "PPL · Giảm cân",
     "description": "Kháng lực theo nhóm cơ kết hợp cardio vừa sức; buổi bỏ lỡ được giữ lại.",
     "schedule": ["Push", "Pull", "Legs", "Cardio", "Push/Pull"],
     "sessions": [PUSH+[CARDIO], PULL+[CARDIO], LEGS, [CARDIO], [PUSH[0], PULL[0], CARDIO]]},
    {"id": "lose_ul", "goal": "lose", "method": "UL", "name": "Upper/Lower · Giảm cân",
     "description": "Luân phiên thân trên, thân dưới và thêm cardio nhẹ; tự chọn ngày tập.",
     "schedule": ["Upper", "Lower", "Upper", "Lower"],
     "sessions": [UPPER+[CARDIO], LOWER, UPPER+[CARDIO], LOWER]},
]


def public_plan(plan):
    return {key: value for key, value in plan.items() if key != "sessions"} | {"sessions_per_cycle": len(plan["sessions"])}


def session_items(plan, session_index):
    session = plan["sessions"][session_index]
    return [{**item, "id": f'{plan["id"]}-{session_index}-{index}-{item["code"]}',
             "rest_seconds": EXERCISE_GUIDE[item["code"]][0],
             "steps": EXERCISE_GUIDE[item["code"]][1]}
            for index, item in enumerate([WARMUP] + session)]
