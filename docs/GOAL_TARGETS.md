# Mục tiêu kcal và protein trong bản demo

Người dùng nhập cân nặng hiện tại, cân nặng mong muốn, ngày muốn đạt mục tiêu, tuổi, chiều cao, thông số sinh học dùng trong công thức và mức vận động. Nếu thiếu một mục, ứng dụng không hiển thị con số mục tiêu tự động. Ngày mục tiêu phải sau hôm nay.

Backend ước tính năng lượng duy trì bằng công thức Mifflin–St Jeor và hệ số vận động 1,2 / 1,375 / 1,55 / 1,725. Chênh lệch cân nặng và số ngày được dùng để tính mức điều chỉnh năng lượng gần đúng, giới hạn ở ±500 kcal/ngày. Mức gợi ý không thấp hơn 1.200 kcal cho lựa chọn nữ hoặc 1.500 kcal cho lựa chọn nam. Protein mặc định là mức cân bằng 1,2 g/kg; người dùng có thể chọn 1,6 g/kg khi theo đuổi tập kháng lực đều. Ví dụ cân nặng 65 kg tương ứng khoảng 80 g hoặc 105 g/ngày. Mức protein dựa trên cân nặng hiện tại và cách tập, không dựa trực tiếp trên tốc độ tăng cân. Chất béo chiếm khoảng 20–30% năng lượng; carb được tính từ năng lượng còn lại sau protein và chất béo (4 kcal/g protein, 4 kcal/g carb, 9 kcal/g chất béo). Kết quả làm tròn để dễ theo dõi.

Đây là mức tham khảo cho người trưởng thành, không dự báo chính xác ngày đạt cân nặng. Công thức đơn giản không mô phỏng thay đổi chuyển hóa theo thời gian, bệnh lý, thai kỳ hoặc nhu cầu riêng. Nếu thời hạn quá gấp hoặc mức tính phải chạm giới hạn, giao diện cảnh báo người dùng. Tổng ăn uống chỉ lấy các món đã xác nhận; dữ liệu dinh dưỡng của món demo hoặc tự nhập có thể chưa chính xác. Gemini dùng các mục tiêu đã tính làm ngữ cảnh để gợi ý thực phẩm và giáo án, không tạo lại con số kcal/protein.

Nguồn tham khảo:

- [Mifflin và cộng sự, công thức dự đoán năng lượng nghỉ](https://pubmed.ncbi.nlm.nih.gov/2305711/)
- [NIDDK Body Weight Planner: nhu cầu năng lượng thay đổi theo hoạt động và thời gian](https://www.niddk.nih.gov/bwp)
- [CDC: mục tiêu giảm cân nên từ từ và thực tế](https://www.cdc.gov/healthy-weight-growth/losing-weight/)
- [International Society of Sports Nutrition: protein khi tập luyện](https://pmc.ncbi.nlm.nih.gov/articles/PMC5477153/)
- [ACSM: khoảng protein cho người tập luyện](https://www.acsm.org/docs/default-source/files-for-resource-library/protein-intake-for-optimal-muscle-maintenance.pdf)
- [Health Canada: khoảng phân bổ carbohydrate và chất béo cho người trưởng thành](https://www.canada.ca/en/health-canada/services/food-nutrition/healthy-eating/dietary-reference-intakes/tables/reference-values-macronutrients.html)
