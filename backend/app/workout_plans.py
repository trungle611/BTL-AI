"""Small, explicit training templates for the first release."""

def exercise(code, name, category, minutes, sets, reps, detail, focus):
    return {"code": code, "name": name, "category": category,
            "duration_minutes": minutes, "sets": sets, "reps": reps, "detail": detail,
            "focus": focus}


WARMUP = exercise("warmup", "Khởi động", "Chuẩn bị", 8, None, None,
                  "Vận động nhẹ và xoay khớp trong biên độ thoải mái.", "Toàn thân")
PUSH = [
    exercise("chest_press", "Machine Chest Press (đẩy ngực máy)", "Push", 12, 3, "8–12",
             "Đẩy tay cầm ngang ngực với vai ổn định và nhịp chậm.", "Ngực giữa · tay sau"),
    exercise("shoulder_press", "Seated Dumbbell Shoulder Press (đẩy vai ngồi)", "Push", 12, 3, "8–12",
             "Đẩy tạ trong tầm vận động thoải mái, không ưỡn lưng.", "Vai trước · vai giữa"),
    exercise("triceps", "Rope Triceps Pushdown (ép tay sau cáp)", "Push", 9, 2, "10–15",
             "Giữ khuỷu gần thân và duỗi cẳng tay có kiểm soát.", "Tay sau"),
    exercise("lateral_raise", "Dumbbell Lateral Raise (nâng ngang vai)", "Push", 8, 2, "12–15",
             "Nâng tạ nhẹ sang hai bên, không nhún vai hay vung người.", "Vai giữa"),
]
PULL = [
    exercise("row", "Seated Cable Row (kéo cáp ngồi)", "Pull", 12, 3, "8–12",
             "Kéo tay cầm về gần bụng, đưa khuỷu về sau mà không ngả thân quá mức.", "Lưng giữa · cơ trám (kéo ngang)"),
    exercise("pulldown", "Lat Pulldown (kéo xô máy)", "Pull", 12, 3, "8–12",
             "Kéo thanh về ngực trên bằng khuỷu tay; không kéo ra sau gáy.", "Cơ xô · độ rộng lưng (kéo dọc)"),
    exercise("biceps", "Dumbbell Biceps Curl (cuốn tạ tay trước)", "Pull", 8, 2, "10–15",
             "Giữ khuỷu gần thân và không đung đưa người.", "Tay trước"),
    exercise("high_row", "Seated High Back Row (kéo lưng cao)", "Pull", 9, 2, "10–12",
             "Dùng tay cầm ngang ngực trên, mở khuỷu vừa phải và kéo về phía mình.", "Lưng trên · vai sau"),
    exercise("back_extension", "Back Extension (duỗi lưng ghế 45°)", "Pull", 8, 2, "10–15",
             "Gập từ hông rồi nâng thân đến thẳng hàng với chân; không ngửa quá mức.", "Lưng dưới · cơ dựng sống · mông"),
]
LEGS = [
    exercise("squat", "Goblet Squat (squat ôm tạ)", "Legs", 12, 3, "8–12",
             "Giữ tạ gần ngực, hạ người trong biên độ kiểm soát với bàn chân vững.", "Đùi trước · mông"),
    exercise("hinge", "Dumbbell Romanian Deadlift (RDL tạ đơn)", "Legs", 12, 3, "8–12",
             "Đẩy hông ra sau, giữ tạ gần chân và lưng trung lập.", "Đùi sau · mông · cơ dựng sống"),
    exercise("calf", "Standing Calf Raise (nhón bắp chân)", "Legs", 7, 2, "12–15",
             "Nhón gót và hạ xuống có kiểm soát, không bật nảy.", "Bắp chân"),
    exercise("leg_curl", "Seated Leg Curl (gập đùi sau máy)", "Legs", 9, 2, "10–15",
             "Chỉnh máy vừa chân, gập gối chậm rồi trả tạ có kiểm soát.", "Đùi sau"),
]
UPPER = [PUSH[0], PULL[0], PUSH[1], PULL[1], PULL[3], PUSH[3]]
LOWER = [LEGS[0], LEGS[1], exercise("plank", "Forearm Plank (plank khuỷu tay)", "Core", 7, 3, "20–40 giây",
                                      "Giữ thân người thẳng và thở đều.", "Cơ trung tâm"), LEGS[3], LEGS[2]]
CARDIO = exercise("cardio", "Đi bộ nhanh trên máy hoặc đạp xe", "Cardio", 20, None, None,
                  "Giữ nhịp độ có thể nói chuyện; điều chỉnh theo thể lực.", "Tim mạch")

EXERCISE_GUIDE = {
    "warmup": (0, ["Đi bộ hoặc đạp xe rất nhẹ 3–5 phút.", "Xoay vai, hông, gối và cổ chân nhẹ nhàng.", "Làm một hiệp nhẹ của động tác chính trước khi tăng tải."]),
    "chest_press": (90, ["Chỉnh ghế để tay cầm ngang giữa ngực, đặt hai chân vững.", "Đẩy tay cầm ra trước với cổ tay thẳng, không khóa khuỷu mạnh.", "Trả tay cầm chậm đến tầm ngực, không nhấc vai khỏi ghế."]),
    "shoulder_press": (90, ["Ngồi hoặc đứng vững, siết nhẹ cơ bụng.", "Đẩy tạ lên trên trong tầm vận động thoải mái.", "Hạ chậm về ngang vai, tránh ưỡn lưng."]),
    "triceps": (60, ["Nắm hai đầu dây cáp, đứng vững và giữ khuỷu gần thân.", "Ép dây xuống bằng cách duỗi khuỷu, không vung vai.", "Trả dây lên chậm đến khi cẳng tay gần ngang sàn."]),
    "row": (90, ["Ngồi vững, đặt chân lên bệ và giữ lưng trung lập.", "Kéo tay cầm về gần bụng bằng cách đưa khuỷu ra sau.", "Thả tạ chậm, không giật thân người."]),
    "pulldown": (90, ["Chỉnh đệm đùi vừa khít, nắm thanh và giữ ngực mở.", "Hạ vai rồi kéo khuỷu xuống, đưa thanh về ngực trên.", "Đưa thanh lên chậm, không ngả người quá mức hoặc kéo sau gáy."]),
    "biceps": (60, ["Cầm hai tạ đơn, đứng vững và giữ khuỷu gần thân.", "Gập khuỷu để nâng tạ, không vung người.", "Hạ tạ chậm về vị trí đầu."]),
    "squat": (120, ["Ôm một tạ đơn sát ngực, đứng chân khoảng rộng vai.", "Hạ hông và gối trong biên độ kiểm soát, giữ lưng trung lập.", "Đẩy chân xuống sàn để đứng lên, tránh gối sụp vào trong."]),
    "hinge": (120, ["Giữ tạ gần đùi, gối hơi chùng.", "Đẩy hông ra sau, hạ tạ dọc chân với lưng trung lập.", "Dùng hông đứng lên, không giật bằng lưng dưới."]),
    "calf": (60, ["Đứng vững và bám điểm tựa nếu cần.", "Nâng gót lên chậm, giữ một nhịp ở trên.", "Hạ gót có kiểm soát."]),
    "plank": (60, ["Chống khuỷu tay dưới vai, duỗi chân ra sau.", "Siết nhẹ bụng và mông, giữ thân người thành một đường thẳng.", "Thở đều; dừng khi không giữ được tư thế."]),
    "cardio": (0, ["Khởi đầu chậm 3–5 phút.", "Đi bộ nhanh hoặc đạp xe ở nhịp có thể nói chuyện.", "Giảm tốc 3–5 phút trước khi dừng."]),
    "lateral_raise": (60, ["Cầm tạ nhẹ, đứng vững và giữ khuỷu hơi chùng.", "Nâng tay sang hai bên đến tầm vai trong biên độ thoải mái.", "Hạ chậm, không nhún vai hoặc vung lưng."]),
    "high_row": (75, ["Chỉnh tay cầm ngang ngực trên và ngồi thẳng.", "Kéo khuỷu ra sau hơi mở sang hai bên, siết nhẹ hai bả vai.", "Trả tạ chậm, không ưỡn lưng hoặc nhún vai."]),
    "back_extension": (75, ["Chỉnh đệm ghế dưới nếp gấp hông, đặt chân chắc.", "Gập từ hông với lưng trung lập, chỉ xuống tới mức kiểm soát được.", "Nâng thân đến thẳng hàng với chân; không ngửa vượt quá đường thẳng."]),
    "leg_curl": (75, ["Chỉnh trục máy ngang gối và đệm vừa cẳng chân.", "Gập gối kéo đệm xuống trong tầm thoải mái.", "Trả tạ chậm, giữ hông trên ghế."]),
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
     "sessions": [PUSH[:3]+[CARDIO]+PUSH[3:], PULL[:3]+[CARDIO]+PULL[3:], LEGS,
                  [CARDIO], [PUSH[0], PULL[0], CARDIO]]},
    {"id": "lose_ul", "goal": "lose", "method": "UL", "name": "Upper/Lower · Giảm cân",
     "description": "Luân phiên thân trên, thân dưới và thêm cardio nhẹ; tự chọn ngày tập.",
     "schedule": ["Upper", "Lower", "Upper", "Lower"],
     "sessions": [UPPER[:4]+[CARDIO]+UPPER[4:], LOWER, UPPER[:4]+[CARDIO]+UPPER[4:], LOWER]},
]


def public_plan(plan):
    sessions = [[WARMUP] + items for items in plan["sessions"]]
    return {key: value for key, value in plan.items() if key != "sessions"} | {
        "sessions_per_cycle": len(sessions),
        "session_exercises": [[{"name": item["name"], "focus": item["focus"],
                                "sets": item["sets"], "reps": item["reps"]} for item in session]
                              for session in sessions]}


def session_items(plan, session_index):
    session = plan["sessions"][session_index]
    return [{**item, "id": f'{plan["id"]}-{session_index}-{index}-{item["code"]}',
             "rest_seconds": EXERCISE_GUIDE[item["code"]][0],
             "steps": EXERCISE_GUIDE[item["code"]][1]}
            for index, item in enumerate([WARMUP] + session)]
