# Hướng dẫn sử dụng Microservices Pipeline (Kaggle OCR + Local Agent)

Dự án này đã được chia tách thành mô hình **Microservices** nhằm 100% tránh xung đột CUDA thư viện. Nó bao gồm 2 môi trường. Dưới đây là cách sử dụng thực tế chuẩn nhất.

---

## 1. Triển khai API Nhận Diện Hình Ảnh trên nền tảng Kaggle (`kaggle_ocr_service`)

Bước này thiết lập đôi mắt Cảm biến (GPU PaddleOCR) trên Cloud, giúp máy tính của bạn hoàn toàn nhẹ nhàng.

**Bước 1.1:** Mở [Kaggle.com](https://www.kaggle.com/) và tạo một Notebook mới.
**Bước 1.2:** Ở bảng cài đặt Notebook (chuột phải), cấu hình như sau:
- **Accelerator**: Chọn `GPU T4 x2` hoặc `GPU P100`.
- **Internet**: Gạt sang `ON`.

**Bước 1.3:** Trên máy tính, zip thư mục `kaggle_ocr_service_zip.zip` hoặc copy nội dung các file trong thư mục `kaggle_ocr_service` ném vào Cell của Kaggle.

**Bước 1.4:** Cài đặt thư viện bằng cách dán vào 1 Cell và chạy:
```bash
!pip install -r requirements_kaggle.txt
```

**Bước 1.5:** (Bảo mật Ngrok) Mở [ngrok.com](https://ngrok.com/), lấy chuỗi Authtoken của bạn. 
Vào `main_fastapi.py`, bỏ comment và điền token của bạn như sau:
```python
NGROK_AUTH_TOKEN = "token_cua_ban_123"
ngrok.set_auth_token(NGROK_AUTH_TOKEN)
public_url = ngrok.connect(8000)
```

**Bước 1.6:** Chạy máy chủ server:
```bash
!python main_fastapi.py
```
> 🎉 **Kết quả:** Terminal Notebook sẽ in ra cái dòng chữ to đùng màu mè `🚀 Kaggle Public URL: https://b1cd-xxxx.ngrok-free.app`. Hãy **Copy URL** này. Mọi thứ trên Kaggle treo ở đó là xong nhiệm vụ!

---

## 2. Các Chế Độ Chạy Phân Hệ `local_agent_backend`

Chạy tại thiết bị Local/Server của bạn nhằm Orchestrate logic.

**Bước 2.1:** Dọn dẹp môi trường cũ (không bắt buộc) và cài đặt thư viện phần Local Backend:
```bash
cd agents/src/parser
pip install -r local_agent_backend/requirements_local.txt
```

**Bước 2.2:** Cấu hình biến môi trường kết nối.
Tạo file `.env` tại thư mục `local_agent_backend/` hoặc set trực tiếp trong Terminal:
```bash
# 1. API Keys & Kaggle Endpoint
export GEMINI_API_KEY="AIx_your_key_here"
export KAGGLE_NGROK_URL="https://b1cd-xxxx.ngrok-free.app"

# 2. Tuỳ chọn: Kết nối MongoDB (Chỉ cấp khi chạy thật)
export MONGO_URI="mongodb+srv://admin:pass@cluster.mongodb.net"
export MONGO_DB="masterTHPT_db"
export MONGO_COLLECTION="exams"
```
*(Lưu ý: Nếu không cấp biến MongoDB, hệ thống vẫn chạy và tạo mảng JSON nội bộ tại thư mục `parsed_results`, thích hợp để test).*

### Xoay Hành Chế Độ Chạy Thực Tế:

#### A. Chạy Demo / Test (Sản sinh JSON file)
Để xác minh độ chính xác của schema và OCR, bạn gọi script giả lập quy trình:
```bash
python tests/test_run.py test_exam.pdf
```
Kết quả JSON cấu trúc hóa sẽ được đẩy ra thư mục `parsed_results/`.

#### B. Chạy Đội Tự Động Toàn Hệ Thống (Production / Backend)
Trong môi trường Backend, khi cung cấp đủ biến `MONGO_*`, Module sẽ tự động:
1. Gửi file tới OCR Server.
2. Ép cục bộ (Grouping) lấy context + image crops.
3. Chờ Gemini hoàn thành Structuring.
4. Tự động Trigger `MongoDBClient().push_exam(...)` ném ID lên Database.

Bạn có thể test trực tiếp luồng hoàn chỉnh tương tự bằng script:
```bash
python tests/test_run.py test_exam.pdf
```
> 🎉 **Kết quả:** Hệ thống sẽ chạy một luồng hoàn toàn Tự Động. Local đẩy File qua API OCR ➔ Phân cấu trúc Logic ➔ Gemini Phân tích & Ép kiểu Pydantic ➔ Móc vào Cluster MongoDB để Store dữ liệu vĩnh viễn! 🚀
