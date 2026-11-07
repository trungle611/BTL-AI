# Giao diện HBTNFIT phiên bản đầu

Phiên bản này ưu tiên hai luồng: **Ăn uống** và **Tập luyện**. Chưa hiển thị quét cơ thể, phân tích cơ mỡ, biểu đồ phức tạp hoặc trang lập thực đơn 7 ngày.

## Bố cục và phong cách

- Desktop tối đa 1440 px; thanh trên 72 px; thanh trái 248 px; khoảng cách giữa hai cột 24 px; đệm thẻ 24 px. Trang tự tăng chiều cao theo nội dung.
- Nền `#121212`, thẻ trắng 6% với viền nhẹ, nút và mục chọn màu cyan. Font Inter với fallback hệ thống. Không dùng blur hoặc hiệu ứng phát sáng mạnh.
- Tablet thu gọn thanh điều hướng thành biểu tượng. Điện thoại dùng một cột theo thứ tự tải ảnh → kết quả → thực đơn → tập luyện; menu mở bằng nút ở thanh trên.

## Luồng ăn uống

1. Kéo thả hoặc chọn JPG/PNG/WEBP tối đa 5 MB. Ảnh được xem trước; có nút đổi, xóa và thử nhận diện lại. File sai loại hoặc quá lớn được báo rõ.
2. Gemini xử lý tự động sau khi chọn ảnh. Trong lúc chờ, giao diện hiển thị “Đang phân tích ảnh…” và khóa gửi lại.
3. Mỗi món được phát hiện có tối đa ba gợi ý. Dinh dưỡng xem trước lấy từ dữ liệu món trong CSDL theo số gam đang nhập, **không lấy số macro do Gemini tự sinh**. Chỉ người dùng chọn món mới bật xác nhận; nhập tay chỉ mở khi gợi ý sai hoặc chưa khớp danh mục.
4. Khi bấm **Xác nhận thêm**, các món được lưu cùng lúc. Mã xác nhận giúp lần gửi lại cùng nội dung không tạo món trùng. Món chờ xác nhận không vào tổng ngày.
5. Thực đơn hôm nay nhóm theo bữa, hiển thị tổng kcal/protein/carb/fat và cho sửa gam, đổi bữa hoặc xóa món. Tổng được tính lại từ các món đã lưu.

## Luồng tập luyện

- Ba bài mẫu hôm nay: khởi động, squat và plank. Mỗi bài có thời lượng, hiệp/lần nếu có và mô tả ngắn.
- Có trạng thái chưa bắt đầu, đang tập, hoàn thành. Tiến độ được lưu theo ngày trên backend, độc lập với nhật ký món ăn.

## Kiểm tra đã thực hiện

- Trình duyệt desktop: nhận diện ảnh hai món bằng Gemini, chỉnh khẩu phần, xác nhận, tổng ngày cập nhật; sửa món đã lưu và tổng tính lại; xem chi tiết bài tập, bắt đầu, hoàn thành.
- Màn hình 390 px: thanh bên ẩn, nội dung thành một cột đúng thứ tự. Ở 1440 px: thanh trên 72 px, thanh bên 248 px, gap và padding 24 px; trang dài theo nội dung.
- Backend: 12 kiểm thử pass, gồm lưu nhiều món, sửa/xóa, trạng thái tập và chống thêm trùng. Frontend build pass và npm audit không báo lỗ hổng.

## Giới hạn dữ liệu demo

Bốn món và số dinh dưỡng hiện là dữ liệu tổng hợp chưa kiểm chứng. Bài tập là template tham khảo. Ảnh thử được tạo bằng AI. Cần thay dữ liệu món bằng nguồn đã xác minh và chạy đánh giá trên ảnh thật trước khi dùng ngoài demo.
