# AIChat-Notes (Flask + SQLite)

Ứng dụng ghi chú đơn giản chạy bằng Flask, lưu trữ nội dung vào file và SQLite, hỗ trợ thư mục, ghim, sắp xếp, tìm kiếm, chia sẻ ghi chú bằng mã, upload ảnh và hỏi đáp AI (Gemini). Có tích hợp gửi email nhắc nhở công việc.

---

## 1) Tính năng chính
- Tài khoản: đăng ký/đăng nhập/đăng xuất
- Quản lý thư mục và ghi chú; ghim (pin) thư mục/ghi chú; sắp xếp theo tên/ngày; tìm kiếm thư mục
- Định dạng, chỉnh sửa ghi chú
- Nội dung ghi chú lưu trong thư mục `notes.db`
- Chia sẻ ghi chú bằng mã và nhập ghi chú từ mã chia sẻ
- Chat hỏi đáp theo nội dung ghi chú bằng Google Gemini (cần API key)
- Đặt email nhắc việc cho ghi chú
- Giao diện sáng/tối và 2 ngôn ngữ vi/en (đổi trong UI)

## 2) Yêu cầu hệ thống
- Windows với Python 3.10+ (khuyên dùng 3.12)
- Tùy chọn: Docker Desktop nếu muốn chạy bằng Docker
- Tùy chọn: Google Gemini API Key (để bật AI) và tài khoản SMTP (để gửi email nhắc việc)

## 3) Cài đặt nhanh (Windows - cmd.exe)

1. Tạo môi trường ảo và kích hoạt
```bat
python -m venv .venv
.venv\Scripts\activate
```

2. Cài thư viện
```bat
python -m pip install --upgrade pip
pip install -r requirements.txt
```

3. Thêm API key để sử dụng chatbot
```
# .env
FLASK_SECRET_KEY=change-me-please
# Thêm API key để sử dụng chatbot
GEMINI_API_KEY=your-gemini-api-key
# (tuỳ chọn) đổi model nếu cần
GEMINI_MODEL=gemini-2.0-flash-exp
```

4. Cấu hình email (tuỳ chọn, dùng cho tính năng nhắc việc qua email)
- Mở file `app.py`, tìm phần cấu hình mail và sửa 2 dòng sau thành tài khoản SMTP của bạn:
  - `app.config['MAIL_USERNAME'] = 'your-email@example.com'`
  - `app.config['MAIL_PASSWORD'] = 'your-app-password-or-smtp-password'`
- Nếu dùng Gmail, nên tạo App Password (không dùng mật khẩu thường). Mặc định server là `smtp.gmail.com:587` và `MAIL_USE_TLS=True`.

5. Chạy ứng dụng
```bat
python app.py
```
- Truy cập: http://127.0.0.1:5000
- Lần đầu chạy sẽ tự tạo `notes.db` và các thư mục cần thiết. Có sẵn tài khoản demo `demo/demo` hoặc bạn có thể đăng ký tài khoản mới.

## 4) Cách sử dụng nhanh
- Tạo thư mục, tạo ghi chú, nhấn ghi chú để mở trang chỉnh sửa
- Nút hình ảnh để upload ảnh
- Ghim thư mục/ghi chú để lên đầu danh sách; sắp xếp theo tên/ngày; tìm kiếm thư mục
- Chia sẻ: Tạo mã chia sẻ từ ghi chú, sau đó nhập mã ở tài khoản khác để sao chép ghi chú
- Chat AI: bật khi có `GEMINI_API_KEY` 
- Đặt nhắc việc: điền email + thời gian tương lai; APScheduler sẽ gửi email

## 5) Chạy bằng Docker
Yêu cầu cài Docker Desktop trên Windows.

1. Build image
```bat
docker build -t aichat-notes .
```

2. Tạo file `.env` như ở bước cài đặt (ít nhất `FLASK_SECRET_KEY`, tuỳ chọn `GEMINI_API_KEY`).

3. Chạy container (đơn giản, không mount — dữ liệu sẽ nằm trong container)
```bat
docker run --name aichat-notes -p 5000:5000 --env-file .env aichat-notes
```

4. (Khuyên dùng) Chạy và mount thư mục dự án để dữ liệu bền vững bên ngoài container
```bat
docker run --name aichat-notes -p 5000:5000 --env-file .env ^
  -v "%cd%\notes":/app/notes ^
  -v "%cd%\notes.db":/app/notes.db ^
  aichat-notes
```
- Truy cập: http://localhost:5000

Ghi chú:
- `Dockerfile` xuất cổng 5000 và chạy `flask run` ở chế độ production env. Nếu muốn public ra mạng LAN, port mapping đã đủ (`-p 5000:5000`).
- Nếu bạn muốn chỉ mount thư mục `notes/` mà không mount `notes.db`, DB sẽ được lưu trong container (mất khi xoá container).

## 6) Giấy phép
Xem `LICENSE-CODE`. Hãy xoá/ẩn thông tin nhạy cảm (`.env`, mật khẩu, API key) trước khi chia sẻ mã nguồn.

