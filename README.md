# HBTNFIT Track 1

Bản khởi tạo ứng dụng nhận diện món Việt, ghi nhật ký dinh dưỡng và lập thực đơn 7 ngày theo tài liệu đề xuất của nhóm. Luồng quét ảnh đã được mở rộng theo yêu cầu mới: Gemini gợi ý tối đa 5 món trong một ảnh, người dùng xác nhận từng món; chỉ mở nhập tay khi gợi ý sai hoặc món bị bỏ sót. Đây là mã nguồn chạy thử, chưa có bộ dữ liệu dinh dưỡng đã kiểm chứng, bộ ảnh đánh giá hay kết quả thực nghiệm thật.

## Chạy trên máy

Yêu cầu Python 3.11+ và Node.js 20+.

```powershell
cd D:\BTLAI
python -m venv .venv
.\.venv\Scripts\python -m pip install -r backend\requirements.txt
cd backend
..\.venv\Scripts\python -m app.seed_demo
..\.venv\Scripts\python -m uvicorn app.main:app --reload
```

Trong terminal khác:

```powershell
cd D:\BTLAI\frontend
npm install
npm run dev
```

Mở `http://localhost:5173`. API docs ở `http://localhost:8000/docs`.

Để gọi Gemini, tạo `backend/.env` từ `.env.example` và điền `GEMINI_API_KEY`. Backend tự nạp file này. Không commit khóa. Không có khóa, chức năng quét ảnh trả lỗi 503 và tìm món thủ công vẫn hoạt động. Thực đơn dùng bộ sinh theo quy tắc, được gắn `generation_mode=rule_fallback`. Khi có khóa, hệ thống gọi Gemini rồi hậu kiểm; nếu kết quả không hợp lệ, dùng dự phòng. Model đang dùng cho demo là `gemini-3.5-flash-lite`.

## Xem demo

Sau khi chạy hai terminal trên, mở `http://localhost:5173` và chọn ảnh; ứng dụng tự gửi ảnh cho Gemini. Có thể chọn **Thử ảnh một món** hoặc **Thử ảnh hai món**. Giao diện hiển thị gợi ý riêng cho từng món; phải chọn món và nhập số gam rồi mới bật nút lưu. Nếu gợi ý sai, bấm **Không đúng món nào? Nhập tay** để tìm trong danh mục; có thể thêm món Gemini bỏ sót. Các ảnh mẫu trong `demo/` được tạo bằng AI, chỉ để thử phần mềm, không dùng làm mẫu đánh giá độ chính xác. Ở tab **Thực đơn 7 ngày**, nhập mục tiêu thử nghiệm và bấm **Tạo thực đơn**; giao diện cho biết kết quả đến từ Gemini hay bộ quy tắc dự phòng.

## Dữ liệu

`app.seed_demo` chỉ thêm bốn món với giá trị **tổng hợp để kiểm thử**, `is_verified=false`. Không dùng những số này làm lời khuyên dinh dưỡng hoặc kết quả nghiên cứu. Mọi kết quả API kèm `source_reference` và cờ kiểm chứng. Nhóm điền `data/foods_template.csv` từ nguồn đã đối chiếu, ghi phiên bản, đơn vị trên 100 g, nguồn cụ thể, người nhập và người kiểm tra trong quy trình review. Nạp bằng:

```powershell
cd D:\BTLAI\backend
..\.venv\Scripts\python -m app.import_foods ..\data\foods_verified.csv
```

Không nhập dữ liệu thật bằng cách đổi cờ `is_verified` khi chưa kiểm tra. Món hỗn hợp cần bảng công thức và cách quy đổi riêng trước khi công bố số liệu.

## Kiểm thử

```powershell
cd D:\BTLAI\backend
..\.venv\Scripts\python -m pytest -q
cd ..\frontend
npm run build
```

Sau khi có dự đoán thật, Bình lưu kết quả theo `data/scan_predictions_template.csv`, rồi chạy `python scripts/evaluate_scan.py ..\data\scan_predictions.csv --split test` từ thư mục `backend`. Script chỉ tính chỉ số từ dữ liệu được cung cấp, không tạo kết quả mẫu.

## Đưa repo lên GitHub và CoReach AI

Repo được tạo cục bộ ở `D:\BTLAI`. Trưởng nhóm tạo repository GitHub riêng, thêm remote rồi `git push -u origin main`. Chia các thẻ việc theo [hướng dẫn phân công](docs/HANDOFF_COREACH.md) trên CoReach AI; mỗi thẻ gắn nhánh, PR và reviewer. Các thành viên không sửa trực tiếp `main`.

API hiện tập trung vào một hồ sơ demo, chưa có đăng nhập hoặc dữ liệu riêng theo người dùng. Không triển khai công khai khi chưa bổ sung xác thực, kiểm soát truy cập và migration. Xem [phân công và kế hoạch](docs/HANDOFF_COREACH.md).
