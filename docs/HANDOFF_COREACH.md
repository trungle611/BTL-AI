# Phân công triển khai HBTNFIT trên CoReach AI

Tài liệu gốc là **bản đề xuất**, không phải bằng chứng đã hoàn thành. Repo hiện có bản chạy thử và dữ liệu tổng hợp. Nhóm cần thực hiện, review và đo đạc các mục sau trước khi nộp.

## Cách đưa lên CoReach AI

1. Tạo project `HBTNFIT Track 1` trên CoReach AI. Đưa tài liệu đề xuất và đường dẫn repo GitHub vào phần tài liệu chung; thêm README này làm hướng dẫn chạy. Không tải `.env`, API key, ảnh riêng tư hoặc file DB lên.
2. Tạo bốn nhánh/nhóm việc bên dưới. Mỗi việc có owner, reviewer, đầu ra, checklist nghiệm thu và link PR. CoReach AI dùng để theo dõi; mã nguồn hợp nhất qua GitHub PR và review.
3. Mỗi thành viên tự ghi các lần dùng AI thật vào `data/ai_usage_log_template.csv`, lưu prompt/response đầy đủ trong nơi nhóm được phép chia sẻ. Không điền hồi tố nội dung bịa.
4. Chỉ merge khi test liên quan pass, có bằng chứng chạy và reviewer khác người viết đồng ý. Cuối mỗi tuần ghi demo đang chạy, lỗi và quyết định cắt phạm vi.

## Bốn phần giao việc

| Thành viên | Issue đầu tiên | Phạm vi chính | Đầu ra và tiêu chí hoàn thành | Reviewer |
|---|---|---|---|---|
| Lê Đình Trung | AI-01 | `backend/app/ai.py`, `core.py` | Đánh giá Gemini trên ảnh một và nhiều món; chỉnh prompt/schema; hậu kiểm planner; test ID lạ, JSON lỗi, timeout. Scan trả từng món với top-3/unknown và không sinh macro. | Bình |
| Nguyễn Minh Hoàng | BE-01 | `backend/app/models.py`, `main.py`, import dữ liệu | Migration, hồ sơ người dùng, API logs/dashboard, giới hạn upload, CSDL món 60 món đầu có nguồn; unit/integration tests. Mỗi kết quả có nguồn và đơn vị. | Trung |
| Nguyễn Danh Nhân | FE-01 | `frontend/` và UX | Xác nhận top-3, nhập gam, nhập tay khi AI lỗi, dashboard, planner, trạng thái lỗi/loading và responsive; ghi hình demo luồng đầy đủ. | Hoàng |
| Nguyễn Xuân Bình | QA-01 | `backend/tests/`, `data/` và benchmark | Protocol gán nhãn, bộ ảnh dev/test tách bữa gần trùng, script Top-1/Top-3/unknown/latency, baseline A/C, bảng lỗi, AI Usage Log. Không dùng test cuối để chỉnh prompt. | Nhân |

**Dữ liệu chung:** mỗi người phụ trách khoảng 30 món và 30 ảnh, kiểm chứng chéo theo vòng Trung → Hoàng → Nhân → Bình → Trung. Trước khi nhập, thống nhất mã món, nguồn, đơn vị và quyền dùng ảnh. Dữ liệu tổng hợp trong seed chỉ dùng kiểm thử kỹ thuật.

## Thứ tự nghiệm thu

1. **Tuần 0–1:** xác nhận phạm vi với giảng viên, tạo repo/board, chốt API và schema, cấp khóa Gemini riêng cho môi trường backend, thử 5–10 ảnh có quyền sử dụng. Kiểm tra ảnh → gợi ý AI trên máy nhóm.
2. **Tuần 2:** nhập 60 món có nguồn, xác nhận khẩu phần, tính macro và lưu nhật ký. Gate A: scan ảnh thật phải chạy; nếu chưa đạt thì sửa pipeline trước.
3. **Tuần 3:** hoàn thiện dashboard, bộ ảnh có nhãn, luồng end-to-end và khóa cách chia dev/test.
4. **Tuần 4:** planner pre-filter/Gemini/post-validator với các hồ sơ thử và edge case. Gate B: nếu chưa hợp lệ, dừng phần lịch tập/chatbot.
5. **Tuần 5:** sửa UX, lỗi và đóng băng tính năng. Gate C: chỉ tiếp tục kiểm thử và sửa lỗi.
6. **Tuần 6:** chạy benchmark thật, xuất CSV/biểu đồ, báo cáo cả ca lỗi, ghi model/prompt/data version và chi phí/thời gian.
7. **Tuần 7:** Báo cáo 1, Báo cáo 2, source/README/demo và AI Usage Log; tổng duyệt trình bày 6 phút.

## Việc còn thiếu so với đề xuất

- Dữ liệu thực 60–150 món, nguồn gốc và review chéo; ảnh 120–150 và quyền sử dụng; hồ sơ thử 30–40.
- Khóa Gemini và kiểm chứng tích hợp thật, retry/timeout/log kỹ thuật có prompt/model version.
- Migration, xác thực người dùng, tách dữ liệu nhiều người dùng và chính sách xóa ảnh/hồ sơ.
- Benchmark, baseline, kết quả thực, báo cáo và video demo. Không điền con số dự kiến thành kết quả.
- Lịch tập và Smart Swap là phần sau hai AI pipeline lõi theo MoSCoW.

## Thẻ việc có thể chép lên CoReach AI

**Tên:** `AI-01 Scan ảnh thật và hậu kiểm`  
**Owner:** Trung  
**Reviewer:** Bình  
**Đầu vào:** API contract, danh mục món đã duyệt, ảnh dev.  
**Việc làm:** gọi Gemini; kiểm tra JSON; ánh xạ alias; trả top-3 hoặc unknown; xử lý lỗi.  
**Done khi:** test tự động pass, 5–10 ảnh dev chạy, không có food_id lạ/macro AI trong kết quả, PR được review, link minh chứng và AI Usage Log đã ghi.

**BE-01 Chuẩn hóa dữ liệu và API.** Owner Hoàng, reviewer Trung. Nhập 60 món đầu bằng CSV có nguồn và phiên bản; thêm migration và kiểm tra đơn vị; hoàn thiện API hồ sơ, nhật ký, dashboard; thêm test 404/422/413/415 và nguồn trong response. Done khi import có đối chiếu chéo, test pass, `/docs` mô tả đúng contract và PR được duyệt.

**FE-01 Hoàn thiện luồng người dùng.** Owner Nhân, reviewer Hoàng. Nối upload ảnh, top-3, xác nhận gam, tìm thủ công, dashboard và planner với API; thêm trạng thái loading/error/unknown và kiểm tra trên điện thoại. Done khi video minh chứng một luồng thành công và một luồng lỗi, build pass, PR được duyệt.

**QA-01 Bộ dữ liệu và đánh giá.** Owner Bình, reviewer Nhân. Chốt quy tắc chụp/gán nhãn, chia dev/test theo bữa, nhập metadata, giữ test cuối riêng; thêm script chạy dự đoán và dùng `scripts/evaluate_scan.py`; lập baseline A/C, bảng lỗi và latency. Done khi có lệnh tái lập, số mẫu rõ ràng, kết quả thật không bị chỉnh tay và AI Usage Log có link tương ứng.

**Phụ thuộc:** AI-01 cần danh mục đầu tiên từ BE-01; FE-01 dựa vào API contract hiện tại; QA-01 cần pipeline AI nhưng có thể chuẩn bị ảnh và protocol ngay. Mỗi người có thể bắt đầu nhánh của mình từ commit khởi tạo.
