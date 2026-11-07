# Giao diện HBTNFIT phiên bản đầu

Phiên bản này ưu tiên hai luồng: **Ăn uống** và **Tập luyện**. Chưa hiển thị quét cơ thể, phân tích cơ mỡ, biểu đồ phức tạp hoặc trang lập thực đơn 7 ngày.

## Bố cục và phong cách

- Desktop tối đa 1440 px; thanh trên 72 px; thanh trái 248 px; khoảng cách giữa hai cột 24 px; đệm thẻ 24 px. Trang tự tăng chiều cao theo nội dung.
- Nền `#121212`, thẻ trắng 6% với viền nhẹ, nút và mục chọn màu cyan. Font Inter với fallback hệ thống. Không dùng blur hoặc hiệu ứng phát sáng mạnh.
- Tablet thu gọn thanh điều hướng thành biểu tượng. Điện thoại dùng một cột; ăn uống theo thứ tự tải ảnh → kết quả → thực đơn. Tập luyện có trang riêng; menu mở bằng nút ở thanh trên.
- Logo Đại học Công nghệ do người dùng cung cấp hiển thị trên thanh trên cạnh tên HBTNFIT.

## Luồng ăn uống

1. Kéo thả hoặc chọn JPG/PNG/WEBP tối đa 5 MB. Ảnh được xem trước; có nút đổi, xóa và thử nhận diện lại. File sai loại hoặc quá lớn được báo rõ.
2. Gemini xử lý tự động sau khi chọn ảnh. Trong lúc chờ, giao diện hiển thị “Đang phân tích ảnh…” và khóa gửi lại.
3. Mỗi món được phát hiện có tối đa ba gợi ý. Dinh dưỡng xem trước lấy từ dữ liệu món trong CSDL theo số gam đang nhập, **không lấy số macro do Gemini tự sinh**. Khi gợi ý sai hoặc không khớp danh mục, người dùng có thể nhập tên món mới, bổ sung dinh dưỡng trên 100 g (có thể để trống), rồi xác nhận. Dữ liệu tự nhập gắn cờ chưa kiểm chứng.
4. Khi bấm **Xác nhận thêm**, các món được lưu cùng lúc. Mã xác nhận giúp lần gửi lại cùng nội dung không tạo món trùng. Món chờ xác nhận không vào tổng ngày.
5. Thực đơn hôm nay nhóm theo bữa, hiển thị tổng kcal/protein/carb/fat và cho sửa gam, đổi bữa hoặc xóa món. Tổng được tính lại từ các món đã lưu.

## Luồng tập luyện

- Trang riêng có bốn giáo án PPL và Upper/Lower, chia theo mục tiêu tăng cơ và giảm cân. Mỗi giáo án hiển thị **thứ tự buổi trong chu kỳ**, không ấn định vào thứ trong tuần; lựa chọn được lưu trên backend.
- Sau khi chọn, danh sách bài của buổi kế tiếp hiện ở đầu trang với thời lượng, hiệp/lần và hướng dẫn. Người dùng ghi nhận **Có đi tập** hoặc **Bỏ lỡ hôm nay**. Bỏ lỡ giữ nguyên buổi cho lần sau; chỉ hoàn thành toàn bộ bài mới chuyển sang buổi kế tiếp vào ngày sau.
- Lịch sử bảy ngày phân biệt có đi, bỏ lỡ, hoàn thành và chưa ghi. “Chưa ghi” không mặc định là bỏ lỡ. Trạng thái bài tập lưu theo ngày và mã bài/giáo án, độc lập với nhật ký món ăn.

## Kiểm tra đã thực hiện

- Trình duyệt desktop: nhận diện ảnh hai món bằng Gemini, chỉnh khẩu phần, xác nhận, tổng ngày cập nhật; sửa món đã lưu và tổng tính lại; xem chi tiết bài tập, bắt đầu, hoàn thành.
- Màn hình 390 px: thanh bên ẩn, nội dung thành một cột đúng thứ tự. Ở 1440 px: thanh trên 72 px, thanh bên 248 px, gap và padding 24 px; trang dài theo nội dung.
- Backend: 14 kiểm thử pass, gồm món ngoài danh mục, lưu nhiều món, sửa/xóa, chọn giáo án, bỏ lỡ giữ nguyên buổi, hoàn thành chuyển buổi và chống thêm trùng. Frontend build pass.
- Trình duyệt: chọn PPL tăng cơ thấy buổi Push đầu tiên cùng bốn bài cụ thể, nút ghi nhận đi tập và lịch sử bảy ngày; món tự nhập 300 kcal được cộng vào tổng; bố cục giáo án ở 390 px không tràn ngang.

## Giới hạn dữ liệu demo

Bốn món và số dinh dưỡng hiện là dữ liệu tổng hợp chưa kiểm chứng. Bài tập là template tham khảo. Ảnh thử được tạo bằng AI. Cần thay dữ liệu món bằng nguồn đã xác minh và chạy đánh giá trên ảnh thật trước khi dùng ngoài demo.
