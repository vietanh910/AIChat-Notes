# AIChat-Notes

Chọn ngôn ngữ / Choose your language:

- Tiếng Việt: [README.vi.md](./README.vi.md)
- English: [README.en.md](./README.en.md)

Mẹo nhanh:
- Cài đặt trên Windows (cmd.exe): tạo venv, `pip install -r requirements.txt`, tạo `.env` (đặt `FLASK_SECRET_KEY` và tuỳ chọn `GEMINI_API_KEY`), rồi `python app.py`.
- Docker: `docker build -t aichat-notes .` và `docker run -p 5000:5000 --env-file .env aichat-notes`.

Xem hướng dẫn chi tiết trong hai tệp trên.
