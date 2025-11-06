# AIChat-Notes (Flask + SQLite)

Ứng dụng ghi chú đơn giản chạy bằng Flask, lưu trữ nội dung vào file và SQLite, hỗ trợ thư mục, ghim, sắp xếp, tìm kiếm, chia sẻ ghi chú bằng mã, upload ảnh và hỏi đáp AI (Gemini). Có tích hợp gửi email nhắc việc bằng APScheduler + SMTP.

---

## 1) Tính năng chính
- Tài khoản: đăng ký/đăng nhập/đăng xuất
- Quản lý thư mục và ghi chú; ghim (pin) thư mục/ghi chú; sắp xếp theo tên/ngày; tìm kiếm thư mục
- Nội dung ghi chú lưu ra file `.md` trong thư mục `notes/`
- Upload ảnh vào `notes/images/` và chèn vào ghi chú
- Chia sẻ ghi chú bằng mã và nhập ghi chú từ mã chia sẻ
- Chat hỏi đáp theo nội dung ghi chú bằng Google Gemini (nếu có API key)
- Đặt email nhắc việc cho ghi chú với APScheduler
- Giao diện 2 ngôn ngữ vi/en (đổi trong UI)

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

3. Tạo file `.env` (cùng cấp với `app.py`)
```ini
# .env
FLASK_SECRET_KEY=change-me-please
# Bật AI hỏi đáp nếu bạn có key Gemini
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
- Nút hình ảnh để upload ảnh (lưu vào `notes/images/`)
- Ghim thư mục/ghi chú để lên đầu danh sách; sắp xếp theo tên/ngày; tìm kiếm thư mục
- Chia sẻ: Tạo mã chia sẻ từ ghi chú, sau đó nhập mã ở tài khoản khác để sao chép ghi chú
- Chat AI: bật khi có `GEMINI_API_KEY` (hỏi các câu liên quan đến nội dung ghi chú)
- Đặt nhắc việc: điền email + thời gian tương lai; APScheduler sẽ gửi email

## 5) Cấu trúc thư mục chính
- `app.py` — điểm vào Flask app, routes, DB, upload, chia sẻ, chat, nhắc việc
- `gemini_service.py` — gọi Google Gemini; đọc `GEMINI_API_KEY` từ `.env`
- `notes.db` — SQLite database
- `notes/` — chứa nội dung ghi chú dạng file (đặt tên theo người dùng)
  - `notes/images/` — ảnh upload
- `templates/` — HTML Jinja2
- `static/` — CSS/JS và assets tĩnh
- `scripts/clear_notes_db.py` — script xoá sạch dữ liệu trong DB (giữ nguyên schema)

## 6) Làm việc với cơ sở dữ liệu (SQLite)

Mở xem database:
- Dùng DB Browser for SQLite (GUI) rồi mở file `notes.db`, hoặc
- Cài `sqlite3` CLI (Windows có thể cài thêm) và chạy:
```bat
sqlite3 notes.db
.tables
.schema
.exit
```

Xoá dữ liệu nhưng giữ bảng (không xoá schema):
- Cách 1: dùng script có sẵn
```bat
.venv\Scripts\activate
python scripts\clear_notes_db.py
```
- Cách 2: chạy thủ công trong SQLite (ví dụ chỉ xoá dữ liệu ghi chú, thư mục, chia sẻ)
```sql
DELETE FROM shared_notes;
DELETE FROM notes;
DELETE FROM folders;
-- tuỳ chọn: Xoá người dùng tự tạo (giữ user demo nếu muốn)
-- DELETE FROM users WHERE username <> 'demo';
VACUUM;
```

Xoá file nội dung ghi chú (không ảnh):
```bat
DEL /Q notes\*.md
```

Lưu ý: Dừng ứng dụng trước khi thao tác DB để tránh khoá file.

## 7) Chạy bằng Docker
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

## 8) Bảo mật và cấu hình
- Đặt `FLASK_SECRET_KEY` đủ mạnh trong `.env`
- Không commit `GEMINI_API_KEY` hay mật khẩu SMTP lên repo
- Nếu dùng Gmail SMTP: bật 2FA + tạo App Password; giữ `MAIL_USE_TLS=True` và port 587
- Mặc định `app.py` chạy `host=127.0.0.1` (chỉ local). Nếu cần truy cập từ máy khác, bạn có thể sửa `app.run(host="0.0.0.0", ...)` hoặc chạy bằng Docker và publish port

## 9) Khắc phục sự cố nhanh
- Không cài được thư viện: nâng cấp pip và kiểm tra version Python
```bat
python -m pip install --upgrade pip
pip install -r requirements.txt
```
- Lỗi cổng bận: đổi port khi chạy Flask hoặc tắt app chiếm port 5000
- Gemini không trả lời: kiểm tra `GEMINI_API_KEY` trong `.env` và kết nối mạng
- Gửi email lỗi: kiểm tra SMTP, user/pass (App Password), firewall, thời gian đặt nhắc việc phải ở tương lai
- Upload ảnh lỗi: kiểm tra định dạng ảnh, dung lượng, và thư mục `notes/images/` có quyền ghi

## 10) Giấy phép
Xem `LICENSE-CODE`. Hãy xoá/ẩn thông tin nhạy cảm (`.env`, mật khẩu) trước khi chia sẻ mã nguồn.

