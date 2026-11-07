# Deploy HBTNFIT lên Vercel để nhóm test

Repository: `https://github.com/trungle611/BTL-AI`. Tạo **hai Vercel projects** từ cùng repository, chọn Root Directory lần lượt là `backend` và `frontend`. Vercel hỗ trợ hai project trong monorepo; backend FastAPI dùng Python Function, frontend dùng Vite.

## 1. Cơ sở dữ liệu

Tạo PostgreSQL (ví dụ Neon qua Vercel Marketplace) và gắn vào project backend. Backend cần `DATABASE_URL` hoặc `POSTGRES_URL` dạng connection string PostgreSQL. Không dùng SQLite trên Vercel: file hệ thống của Functions không lưu dữ liệu bền vững.

## 2. Project backend

- Root Directory: `backend`.
- Framework Preset: FastAPI nếu Vercel tự nhận; entrypoint hiện là `app/main.py`.
- Python: 3.12 theo `.python-version`.
- Environment Variables:
  - `DATABASE_URL` hoặc `POSTGRES_URL`: connection string PostgreSQL từ database integration.
  - `GEMINI_API_KEY`: khóa mới, chỉ đặt ở backend. Khóa cũ đã từng gửi qua chat nên cần thay trước khi công khai.
  - `GEMINI_MODEL=gemini-3.5-flash-lite`.
  - `SEED_DEMO=1` để thêm bốn món tổng hợp chưa kiểm chứng khi database trống.
  - `REQUIRE_VISITOR_ID=1` để mỗi trình duyệt có phiên test riêng.
  - `ALLOW_VERCEL_PREVIEWS=1` nếu muốn test các bản Preview.
  - `FRONTEND_ORIGINS=https://TEN-FRONTEND.vercel.app` sau khi có tên miền frontend chính thức.
- Kiểm tra `https://TEN-BACKEND.vercel.app/api/health` trả `status: ok` và `ai_configured: true`.

## 3. Project frontend

- Root Directory: `frontend`.
- Framework Preset: Vite; build `npm run build`; output `dist`.
- Environment Variable **build time**: `VITE_API_URL=https://TEN-BACKEND.vercel.app` (không có dấu `/` cuối).
- Deploy lại frontend sau khi sửa biến môi trường.

## 4. Kiểm thử sau deploy

1. Mở frontend trên hai trình duyệt khác nhau. Kiểm tra hồ sơ, thực đơn và giáo án không nhìn thấy dữ liệu của nhau.
2. Chọn ảnh demo, chờ Gemini gợi ý, xác nhận món và kiểm tra tổng dinh dưỡng.
3. Vào Cá nhân, nhập **số liệu giả để test**, chạy AI phân tích và chọn một cách ăn cùng một giáo án.
4. Vào Tập luyện, mở chi tiết bài, ghi nhận có đi tập hoặc bỏ lỡ.
5. Nếu scan/AI báo lỗi, xem Function Logs của project backend; nếu trình duyệt báo lỗi CORS, kiểm tra `FRONTEND_ORIGINS`.

## Giới hạn bản test

Mã phiên được lưu trong `localStorage` của từng trình duyệt, **chưa phải đăng nhập/xác thực**. Người dùng xóa dữ liệu trình duyệt sẽ mất liên kết tới phiên cũ. Chỉ dùng số liệu giả khi test; chưa dùng cho dữ liệu sức khỏe thật. Món dinh dưỡng seed là dữ liệu tổng hợp chưa kiểm chứng. Cần tài khoản, xác thực, migration chính thức và quota AI trước khi công khai cho người dùng thật.
