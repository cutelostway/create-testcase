# Thông tin chi tiết cho từng flow (Markdown)

## A. Tạo mới Project  
> Ở những mục có nhiều lựa chọn, mặc định chọn những thông tin được đánh dấu **Default**.

### A.1. Name
- `{Tên project}` *(user nhập khi mô tả chức năng, **không bắt buộc**).*

### A.2. Description
- `{Mô tả tổng quan về project}` *(user nhập khi mô tả chức năng, **không bắt buộc**).*

### A.3. Language
- **Default:** Vietnamese

### A.4. Writing Style & Tone
Chọn **một** trong các phong cách sau:
1. **Natural and Clear** *(Default)* — Ngôn ngữ tự nhiên, trôi chảy, rõ ràng cho chuyên gia kiểm thử. Viết test case theo lối diễn đạt gần gũi, dễ đọc.
2. **Professional and Context-Appropriate** — Giữ tông chuyên nghiệp, dùng thuật ngữ chuẩn ngành, bảo đảm rõ ràng.
3. **Concise and Direct** — Ngắn gọn, trực tiếp, tránh rườm rà nhưng vẫn đủ ý và khả thi khi thực thi.
4. **Clear and Practical** — Thực tế, dễ hiểu, tập trung vào các bước có thể thực thi ngay.
5. **Readable and User-Friendly** — Dễ quét/đọc nhanh, tối ưu cho khả năng nắm bắt của tester.
6. **Industry Standard, Not Complex** — Dùng thuật ngữ chuẩn ngành, không phức tạp quá mức, dễ tiếp cận.
7. **Direct and Instructional** — Giọng điệu hướng dẫn trực tiếp, chỉ dẫn từng bước rõ ràng với kết quả mong đợi cụ thể.

### A.5. Checklist setting – Detail level  
> Parameter: `{1}` (user chọn **01** mức)

1. **Comprehensive Testing (Thorough)** *(Default)*  
   Bao quát tối đa, gồm tình huống hiếm, edge case phức tạp, kỹ thuật xác nhận nâng cao:
   - Tất cả luồng người dùng và workflow
   - Edge case phức tạp, điều kiện biên
   - Tình huống hiếm và kết hợp bất thường
   - Negative testing mở rộng
   - Kiểm thử bảo mật/hiệu năng nâng cao
2. **Standard Testing (Balanced)**  
   Bao phủ luồng chính, edge case thường gặp, lỗi/ngoại lệ tiêu chuẩn:
   - Luồng chính và đường rẽ nhánh phổ biến
   - Edge case/biên thường gặp
   - Tình huống xử lý lỗi tiêu chuẩn
   - Kiểm tra validate dữ liệu (nhiều kiểu)
   - Negative testing cơ bản
3. **Minimal Testing (Essential)**  
   Tối thiểu, tập trung chức năng cốt lõi và luồng quan trọng:
   - Chỉ happy path
   - Xác nhận chức năng thiết yếu
   - Validate đầu vào cơ bản (hợp lệ/không hợp lệ)
   - Quy tắc nghiệp vụ trọng yếu
   - Tiêu chí Pass/Fail đơn giản

### A.6. Testing type (các category cần tạo test case)  
> Parameter: `{1,2,3}` (user có thể chọn **nhiều**)

1) Function testing  
2) Include Header And Footer  
3) UI Testing  
4) Security Testing  
5) Performance Testing  
6) Accessibility Testing  
7) Data Validation Testing

### A.7. Priority Levels  
> Người dùng chọn **loại ảnh hưởng**, AI xác định **độ ưu tiên** tương ứng.  
> **Default loại ảnh hưởng:** *Business Impact*.

**Loại ảnh hưởng:**
- **Business Impact** *(Default)* — Ưu tiên theo ảnh hưởng đến vận hành, doanh thu, giao dịch lõi.  
- **User Impact** — Ưu tiên theo độ ảnh hưởng đến trải nghiệm, khả năng hoàn thành tác vụ.  
- **Data Integrity Focus** — Ưu tiên theo rủi ro sai lệch/mất/hỏng dữ liệu.

**Mức ưu tiên:**
- `[1]` Critical  
- `[2]` High  
- `[3]` Medium  
- `[4]` Low

### A.8. Exclusion Rules
1) Skip Common UI Sections  
2) Skip Non-functional Areas  
3) Skip Third-party Integrations  
4) Skip Redundant Test Cases  
5) Skip Obvious Actions  
6) Skip Minor Visual Issues

### A.9. Test Steps Detail Level
1. **Low Detail** — Tóm tắt hành động/chủ đạo và kết quả, bỏ qua bước thường lệ; phù hợp tester giàu kinh nghiệm.  
2. **Medium Detail** *(Default)* — Gom nhóm bước khi có thể nhưng vẫn rõ ràng; tập trung thao tác chính, kết quả, và **data quan trọng**.  
3. **High Detail** — Ghi chi tiết từng hành động và kết quả mong đợi, từng bước, kèm toàn bộ **test data** cần thiết.

---

## B. Mô tả chức năng

### B.1. Spec
- User nhập thông tin mô tả cho chức năng cần test (tự do nội dung).

### B.2. Screenshot
- User có thể upload ảnh màn hình để mô tả rõ hơn chức năng.

### B.3. File
- User có thể upload file spec kèm theo.

---

## C. Tạo checklist

**Mô tả:**  
- Checklist cần **phân nhóm theo mục đích/chức năng** và **sắp xếp happy case trước**, để reviewer theo dõi dễ.  
- Cấu trúc phân cấp:  
  - **Level 1:** *Category*  
  - **Level 2 (nếu có):** *Sub-category*  
  - **Level thấp nhất:** *Các checklist item* (đơn vị kiểm thử)

---

## D. Review checklist

### D.1. Comment test case hiện tại
- Mô tả nội dung cần **cập nhật/xóa** test case, **dựa vào ID** test case.

### D.2. Comment test case (thêm mới)
- Mô tả test case cần **thêm mới**, có thể **upload image** minh họa.

---

## E. Tạo test case

**Trường thông tin của test case:**
- **ID Testcase:** `TC001`, `TC002`, …  
- **Title**  
- **Checklist (tương ứng)**  
- **Category**  
- **Sub-Category**  
- **Priority**  
- **Pre-condition**  
- **Description**  
- **Step**  
- **Expected Result**  
- **Test Data** *(tạo dưới dạng **HTML table** để dễ copy)*

**Ngôn ngữ (E.2):**  
- **Tiếng Việt** *(mặc định)* — có thể tùy chọn chuyển sang **Tiếng Anh**.

**Test data example (E.3):**  
- User mô tả ví dụ test data; AI dựa vào đó để sinh **test data** phù hợp cho từng case.
