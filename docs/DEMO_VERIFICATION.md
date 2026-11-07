# Kiểm tra demo ngày 7 tháng 11 năm 2026

Đây là biên bản smoke test kỹ thuật, **không phải kết quả benchmark**. Ảnh phở được tạo bằng AI để kiểm tra luồng phần mềm; bốn bản ghi món và macro là dữ liệu tổng hợp, chưa xác minh nguồn dinh dưỡng.

| Bước | Quan sát |
|---|---|
| Kết nối Gemini | Model `gemini-3.5-flash-lite` trả lời thành công qua API. Model cũ `gemini-2.5-flash` trả 404 cho tài khoản dùng thử. |
| Quét ảnh tổng hợp | Gemini gợi ý `Phở bò`; API trả `needs_confirmation` với `DEMO_001`. |
| Ảnh hai món tổng hợp | Gemini tách `Phở bò` và `Cơm tấm sườn`; API ánh xạ thành `DEMO_001` và `DEMO_002`. Giao diện buộc chọn từng món trước khi bật nút lưu. |
| Xác nhận và nhật ký | Giao diện lưu 250 g `DEMO_001`; dashboard hiển thị 250 kcal theo dữ liệu tổng hợp 100 kcal/100 g. Đây chỉ là phép kiểm tra công thức. |
| Thực đơn | API và giao diện tạo kế hoạch 7 ngày bằng Gemini; hậu kiểm ID, số bữa và năng lượng đạt trên lần chạy demo. |
| Kiểm thử | 7 pytest pass; frontend Vite build pass; npm audit không báo lỗ hổng. |

Kiểm thử sau thay đổi nhiều món: 9 pytest pass, frontend build pass. Trên giao diện, đã thử nhánh “Không đúng món nào? Nhập tay”, quay lại gợi ý, chọn hai món và lưu cùng lúc; dashboard hiển thị hai bản ghi mới.

Ảnh thử: [pho_bo_synthetic.png](../demo/pho_bo_synthetic.png). Prompt tạo ảnh: “Photorealistic natural smartphone food photo for a software demo: a single bowl of Vietnamese phở bò on a plain wooden table, visible rice noodles, sliced beef, herbs and clear broth, overhead three-quarter angle, natural daylight, realistic restaurant setting, no other dishes, no people, no text, square composition.” Tạo bằng công cụ ImageGen tích hợp.

Ảnh hai món: [pho_bo_com_tam_synthetic.png](../demo/pho_bo_com_tam_synthetic.png). Prompt: “Photorealistic natural smartphone photo for testing a Vietnamese food recognition app. On one restaurant table, show exactly two clearly separate dishes side by side: one bowl of phở bò with rice noodles, sliced beef, broth and herbs; one plate of cơm tấm with rice and grilled pork chop. Both dishes fully visible and distinct, overhead three-quarter view, daylight, no other food or drinks, no people, no labels or text, square composition.” Tạo bằng ImageGen tích hợp.

Chưa được kiểm tra: ảnh món thật đa dạng, độ chính xác Top-1/Top-3, ước lượng khẩu phần, nguồn dinh dưỡng, p95 latency, an toàn thực đơn ngoài dữ liệu demo, nhiều người dùng và triển khai công khai. Các phần này cần dữ liệu và review thật của nhóm theo [kế hoạch phân công](HANDOFF_COREACH.md).
