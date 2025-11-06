from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    jsonify,
    session,
    flash,
    send_from_directory,
)
import sqlite3
import os
import re
import secrets
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from flask_cors import CORS
from html import unescape as html_unescape
from dotenv import load_dotenv
from gemini_service import ask_gemini
from flask_mail import Mail, Message
from flask_apscheduler import APScheduler
# Load environment variables
load_dotenv()

app = Flask(__name__)

# --- CẤU HÌNH SCHEDULER VÀ MAIL ---

# Cấu hình Scheduler
scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()

# Cấu hình Flask-Mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your-mail@example.com'  # <-- THAY BẰNG EMAIL CỦA BẠN
app.config['MAIL_PASSWORD'] = 'your-app-password-or-smtp-password' # <-- THAY BẰNG MẬT KHẨU ỨNG DỤNG MAIL
mail = Mail(app)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-change-me")


# Language translations
TRANSLATIONS = {
    'vi': {
        # Common
        'app_name': 'NoteApp',
        'home': 'Trang chính',
        'logout': 'Đăng xuất',
        'login': 'Đăng nhập',
        'register': 'Đăng ký',
        'cancel': 'Hủy',
        'save': 'Lưu',
        'delete': 'Xóa',
        'edit': 'Chỉnh sửa',
        'create': 'Tạo',
        'back': 'Quay lại',

        # Auth pages
        'welcome_back': 'Chào mừng trở lại',
        'login_subtitle': 'Đăng nhập để tiếp tục với ghi chú của bạn',
        'username': 'Tên đăng nhập',
        'password': 'Mật khẩu',
        'username_placeholder': 'Nhập tên đăng nhập...',
        'password_placeholder': 'Nhập mật khẩu...',
        'create_account': 'Tạo tài khoản mới',
        'register_subtitle': 'Bắt đầu hành trình ghi chú của bạn',
        'register_username_placeholder': 'Chọn tên đăng nhập...',
        'register_password_placeholder': 'Tạo mật khẩu...',
        'have_account': 'Đã có tài khoản?',
        'no_account': 'Chưa có tài khoản?',
        'login_now': 'Đăng nhập ngay',
        'register_now': 'Tạo tài khoản ngay',

        # Main page
        'folders': 'Thư mục',
        'new_folder': 'Thư mục mới',
        'all_notes': 'Tất cả ghi chú',
        'create_note': 'Tạo ghi chú mới',
        'create_note_placeholder': ' Tạo ghi chú mới...',
        'no_notes': 'Chưa có ghi chú',
        'no_notes_subtitle': 'Tạo ghi chú đầu tiên để bắt đầu!',
        'note_click_open': 'Click để mở',

        # Note editing
        'edit_note': 'Chỉnh sửa ghi chú',
        'view_note': 'Xem ghi chú',
        'save_changes': 'Lưu thay đổi',
        'add_image': 'Thêm hình ảnh',
        'insert_table': 'Chèn bảng',
        'untitled': 'Không có tiêu đề',
        'start_writing': 'Bắt đầu viết...',
        'back_to_top': 'Lên đầu trang',

        # Table modal
        'insert_table_modal': 'Chèn bảng',
        'select_size': 'Chọn nhanh kích thước (tối đa 10x10):',

        # Tooltips
        'tooltip_home': 'Về trang chính',
        'tooltip_logout': 'Đăng xuất',
        'tooltip_login': 'Đăng nhập',
        'tooltip_add_folder': 'Thêm thư mục mới',
        'tooltip_edit_folder': 'Chỉnh sửa thư mục',
        'tooltip_delete_folder': 'Xóa thư mục và tất cả ghi chú bên trong',
        'tooltip_create_note': 'Tạo ghi chú mới',
        'tooltip_edit_note': 'Chỉnh sửa ghi chú',
        'tooltip_delete_note': 'Xóa ghi chú',
        'tooltip_save': 'Lưu thay đổi',
        'tooltip_cancel': 'Hủy bỏ',
        'tooltip_back_list': 'Quay lại danh sách ghi chú',
        'tooltip_add_image': 'Thêm hình ảnh',
        'tooltip_insert_table': 'Chèn bảng',
        'tooltip_chat': 'Trò chuyện với trợ lý',

        # Messages
        'saved_successfully': 'Đã lưu thành công!',
        'upload_failed': 'Tải lên thất bại',
        'delete_confirm_note': 'Xóa ghi chú này?',
        'delete_confirm_folder': 'Xóa thư mục này và tất cả ghi chú bên trong?',

        # Sorting - NEW
        'sort_by': 'Sắp xếp theo',
        'sort_by_name': 'Tên',
        'sort_by_date': 'Ngày tạo',
        'sort_order_asc': 'Tăng dần',
        'sort_order_desc': 'Giảm dần',
        'search_folders': 'Tìm kiếm folder...',

        # Language
        'language': 'Ngôn ngữ',
        'vietnamese': 'Tiếng Việt',
        'english': 'English',

        # Settings - NEW
        'settings': 'Cài đặt',
        'theme': 'Giao diện',
        'light_mode': 'Sáng',
        'dark_mode': 'Tối',
        'app_info': 'Thông tin ứng dụng',
        'version': 'Phiên bản',
        'author': 'Tác giả',
        'description': 'Mô tả',
        'app_description': 'Ứng dụng ghi chú đơn giản và mạnh mẽ',
        'close': 'Đóng',
        'settings_saved': 'Đã lưu cài đặt!',

        # Share feature - NEW
        'share_note': 'Chia sẻ ghi chú',
        'share_code': 'Mã chia sẻ',
        'generate_share_code': 'Tạo mã chia sẻ',
        'copy_share_code': 'Sao chép mã',
        'import_note': 'Nhập ghi chú',
        'import_note_placeholder': 'Nhập mã chia sẻ...',
        'import_note_btn': 'Nhập ghi chú',
        'share_code_copied': 'Đã sao chép mã chia sẻ!',
        'note_imported_successfully': 'Đã nhập ghi chú thành công!',
        'invalid_share_code': 'Mã chia sẻ không hợp lệ!',
        'share_code_not_found': 'Không tìm thấy ghi chú với mã này!',
        'share_modal_title': 'Chia sẻ ghi chú',
        'import_modal_title': 'Nhập ghi chú từ mã chia sẻ',

        # Chat UI
        'chat_with_ai': 'Hỏi ghi chú',
        'type_your_message': 'Nhập câu hỏi của bạn... (Enter để gửi)',
        'send': 'Gửi',
        'chat_welcome': 'Xin chào! Mình có thể trả lời các câu hỏi dựa trên nội dung trong ghi chú này. Bạn muốn biết gì?',
        'error_no_response': 'Không có phản hồi phù hợp.',
        'error_sending_message': 'Có lỗi khi gửi tin nhắn. Vui lòng thử lại.',
    },
    'en': {
        # Common
        'app_name': 'NoteApp',
        'home': 'Home',
        'logout': 'Logout',
        'login': 'Login',
        'register': 'Register',
        'cancel': 'Cancel',
        'save': 'Save',
        'delete': 'Delete',
        'edit': 'Edit',
        'create': 'Create',
        'back': 'Back',

        # Auth pages
        'welcome_back': 'Welcome back',
        'login_subtitle': 'Login to continue with your notes',
        'username': 'Username',
        'password': 'Password',
        'username_placeholder': 'Enter username...',
        'password_placeholder': 'Enter password...',
        'create_account': 'Create new account',
        'register_subtitle': 'Start your note-taking journey',
        'register_username_placeholder': 'Choose username...',
        'register_password_placeholder': 'Create password...',
        'have_account': 'Already have an account?',
        'no_account': "Don't have an account?",
        'login_now': 'Login now',
        'register_now': 'Register now',

        # Main page
        'folders': 'Folders',
        'new_folder': 'New Folder',
        'all_notes': 'All Notes',
        'create_note': 'Create Note',
        'create_note_placeholder': '✨ Create a new note...',
        'no_notes': 'No notes yet',
        'no_notes_subtitle': 'Create your first note to get started!',
        'note_click_open': 'Click to open',

        # Note editing
        'edit_note': 'Edit Note',
        'view_note': 'View Note',
        'save_changes': 'Save Changes',
        'add_image': 'Add Image',
        'insert_table': 'Insert Table',
        'untitled': 'Untitled',
        'start_writing': 'Start writing...',
        'back_to_top': 'Back to top',

        # Table modal
        'insert_table_modal': 'Insert Table',
        'select_size': 'Quick select size (max 10x10):',

        # Tooltips
        'tooltip_home': 'Go to home',
        'tooltip_logout': 'Logout',
        'tooltip_login': 'Login',
        'tooltip_add_folder': 'Add new folder',
        'tooltip_edit_folder': 'Edit folder',
        'tooltip_delete_folder': 'Delete folder and all notes inside',
        'tooltip_create_note': 'Create new note',
        'tooltip_edit_note': 'Edit note',
        'tooltip_delete_note': 'Delete note',
        'tooltip_save': 'Save changes',
        'tooltip_cancel': 'Cancel',
        'tooltip_back_list': 'Back to notes list',
        'tooltip_add_image': 'Add image',
        'tooltip_insert_table': 'Insert table',
        'tooltip_chat': 'Chat with assistant',

        # Messages
        'saved_successfully': 'Saved successfully!',
        'upload_failed': 'Upload failed',
        'delete_confirm_note': 'Delete this note?',
        'delete_confirm_folder': 'Delete this folder and all its notes?',

        # Sorting - NEW
        'sort_by': 'Sắp xếp theo',
        'sort_by_name': 'Tên',
        'sort_by_date': 'Ngày tạo',
        'sort_order_asc': 'Tăng dần',
        'sort_order_desc': 'Giảm dần',
        'search_folders': 'Tìm kiếm folder...',

        # Language
        'language': 'Language',
        'vietnamese': 'Tiếng Việt',
        'english': 'English',

        # Settings - NEW
        'settings': 'Settings',
        'theme': 'Theme',
        'light_mode': 'Light',
        'dark_mode': 'Dark',
        'app_info': 'App Information',
        'version': 'Version',
        'author': 'Author',
        'description': 'Description',
        'app_description': 'Simple and powerful note-taking app',
        'close': 'Close',
        'settings_saved': 'Settings saved!',

        # Share feature - NEW
        'share_note': 'Share Note',
        'share_code': 'Share Code',
        'generate_share_code': 'Generate Code',
        'copy_share_code': 'Copy Code',
        'import_note': 'Import Note',
        'import_note_placeholder': 'Enter share code...',
        'import_note_btn': 'Import Note',
        'share_code_copied': 'Share code copied!',
        'note_imported_successfully': 'Note imported successfully!',
        'invalid_share_code': 'Invalid share code!',
        'share_code_not_found': 'Note not found with this code!',
        'share_modal_title': 'Share Note',
        'import_modal_title': 'Import Note from Share Code',

        # Chat UI
        'chat_with_ai': 'Ask this note',
        'type_your_message': 'Type your question... (Enter to send)',
        'send': 'Send',
        'chat_welcome': 'Hi! I can answer questions based on the content in this note. What would you like to know?',
        'error_no_response': 'No response available.',
        'error_sending_message': 'Error sending message. Please try again.',
    }
}

def send_reminder_email(app_context, recipient_email, note_title, note_content):
    """Hàm chạy nền để gửi email nhắc nhở."""
    with app_context:
        try:
            # Tạo nội dung email ở dạng HTML
            html_body = f"""
            <p>Chào bạn,</p>
            <p>Đây là lời nhắc cho ghi chú của bạn:</p>
            <hr>
            <h3>Tiêu đề: {note_title}</h3>
            <h4>Nội dung:</h4>
            <div>{note_content}</div>
            <hr>
            <p>Trân trọng,<br>Đội ngũ NoteApp.</p>
            """
            
            # Tạo một phiên bản văn bản thuần để dự phòng
            plain_text_content = re.sub('<[^<]+?>', '\\n', note_content).strip()
            plain_text_body = f"Chào bạn,\n\nĐây là lời nhắc cho ghi chú của bạn:\n\nTiêu đề: {note_title}\nNội dung:\n{plain_text_content}\n\nTrân trọng,\nĐội ngũ NoteApp."

            msg = Message(
                subject=f"Lời nhắc cho ghi chú: {note_title}",
                sender=('NoteApp', app.config['MAIL_USERNAME']),
                recipients=[recipient_email]
            )

            # Gán nội dung văn bản thuần vào msg.body
            msg.body = plain_text_body
            
            # Gán nội dung HTML vào msg.html
            msg.html = html_body

            mail.send(msg)
            print(f"Đã gửi email nhắc nhở thành công tới {recipient_email}")
        except Exception as e:
            print(f"Lỗi khi gửi email: {e}")

def get_current_language():
    return session.get('language', 'vi')

def t(key):
    """Translation function"""
    lang = get_current_language()
    return TRANSLATIONS.get(lang, {}).get(key, key)

@app.route('/set_language/<language>')
def set_language(language):
    if language in ['vi', 'en']:
        session['language'] = language
    return redirect(request.referrer or url_for('index'))

@app.route('/set_theme/<theme>')
def set_theme(theme):
    if theme in ['light', 'dark']:
        session['theme'] = theme
    return redirect(request.referrer or url_for('index'))

def get_current_theme():
    return session.get('theme', 'light')

@app.context_processor
def inject_language():
    return {
        'current_language': get_current_language(),
        'current_theme': get_current_theme(),
        't': t,
        'current_user': {
            'id': session.get('user_id'),
            'username': session.get('username'),
        }
    }


DB_FILE = "notes.db"
NOTES_DIR = "notes"
UPLOAD_IMAGE_FOLDER = os.path.join(NOTES_DIR, "images")

app.config["UPLOAD_IMAGE_FOLDER"] = UPLOAD_IMAGE_FOLDER
# app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB limit for videos

CORS(
    app,
    resources={r"/upload_image": {"origins": "*"}},
)

if not os.path.exists(UPLOAD_IMAGE_FOLDER):
    os.makedirs(UPLOAD_IMAGE_FOLDER)


def get_conn():
    conn = sqlite3.connect(DB_FILE)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def sanitize_filename(name: str) -> str:
    """Return a safe filename for Windows/macOS/Linux from a title."""
    # Replace invalid characters with underscore
    name = re.sub(r'[<>:"/\\|?*\0-\x1F]', "_", name)
    # Collapse whitespace
    name = re.sub(r"\s+", " ", name).strip()
    # Avoid trailing dots/spaces (Windows)
    name = name.rstrip(" .")
    return name or "untitled"


def init_db():
    with get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS folders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                pinned INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                filename TEXT,
                folder_id INTEGER,
                user_id INTEGER NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                pinned INTEGER DEFAULT 0,
                FOREIGN KEY (folder_id) REFERENCES folders (id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
            """
        )

        # Table for shared notes (share_code)
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS shared_notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                share_code TEXT UNIQUE NOT NULL,
                note_id INTEGER NOT NULL,
                original_user_id INTEGER NOT NULL,
                title TEXT,
                content TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(note_id) REFERENCES notes(id) ON DELETE CASCADE,
                FOREIGN KEY(original_user_id) REFERENCES users(id) ON DELETE CASCADE
            )
            """
        )

        conn.commit()

        # Ensure a default user exists (id=1) for legacy data
        c = conn.cursor()
        c.execute("SELECT id FROM users WHERE id = 1")
        if not c.fetchone():
            c.execute(
                "INSERT INTO users (id, username, password_hash, created_at) VALUES (1, ?, ?, ?)",
                ("demo", generate_password_hash("demo"), datetime.utcnow().isoformat()),
            )
            conn.commit()

        migrate_schema(conn)

        # Seed initial folders for demo user only if empty after migration
        c.execute("SELECT COUNT(1) FROM folders")
        if c.fetchone()[0] == 0:
            c.execute("INSERT OR IGNORE INTO folders (name, user_id) VALUES (?, ?)", ("Principal", 1))
            c.execute("INSERT OR IGNORE INTO folders (name, user_id) VALUES (?, ?)", ("Templates", 1))
            conn.commit()


def migrate_schema(conn: sqlite3.Connection):
    c = conn.cursor()

    # Check and add user_id and created_at to folders
    c.execute("PRAGMA table_info(folders)")
    cols = [row[1] for row in c.fetchall()]
    needs_rebuild_folders = ("user_id" not in cols or "created_at" not in cols or
                           ("name" in cols and unique_is_global(conn, "folders", "name")))

    if needs_rebuild_folders:
        # Rebuild folders table
        c.execute("BEGIN TRANSACTION")
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS folders_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(name, user_id),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
            """
        )
        # Copy old data with defaults
        if "user_id" in cols and "created_at" in cols:
            c.execute("INSERT INTO folders_new (id, name, user_id, created_at) SELECT id, name, user_id, created_at FROM folders")
        elif "user_id" in cols:
            c.execute("INSERT INTO folders_new (id, name, user_id, created_at) SELECT id, name, user_id, CURRENT_TIMESTAMP FROM folders")
        else:
            c.execute("INSERT INTO folders_new (id, name, user_id, created_at) SELECT id, name, 1, CURRENT_TIMESTAMP FROM folders")
        c.execute("DROP TABLE folders")
        c.execute("ALTER TABLE folders_new RENAME TO folders")
        c.execute("COMMIT")

    # Check and add user_id and created_at to notes
    c.execute("PRAGMA table_info(notes)")
    cols = [row[1] for row in c.fetchall()]
    needs_rebuild_notes = ("user_id" not in cols or "created_at" not in cols or
                          ("title" in cols and unique_is_global(conn, "notes", "title")))

    if needs_rebuild_notes:
        c.execute("BEGIN TRANSACTION")
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS notes_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                filename TEXT,
                folder_id INTEGER,
                user_id INTEGER NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (folder_id) REFERENCES folders(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                UNIQUE(title, folder_id, user_id)
            )
            """
        )

        # Handle migration based on which columns exist
        if "user_id" in cols and "created_at" in cols:
            # Both columns exist
            c.execute(
                """
                INSERT INTO notes_new (id, title, filename, folder_id, user_id, created_at)
                SELECT n.id, n.title, n.filename, n.folder_id, n.user_id, n.created_at
                FROM notes n
                """
            )
        elif "user_id" in cols:
            # Only user_id exists, need to add created_at
            c.execute(
                """
                INSERT INTO notes_new (id, title, filename, folder_id, user_id, created_at)
                SELECT n.id, n.title, n.filename, n.folder_id, n.user_id, CURRENT_TIMESTAMP
                FROM notes n
                """
            )
        else:
            # Neither column exists, derive user_id from folder and add created_at
            c.execute(
                """
                INSERT INTO notes_new (id, title, filename, folder_id, user_id, created_at)
                SELECT n.id, n.title, n.filename, n.folder_id, COALESCE(f.user_id, 1), CURRENT_TIMESTAMP
                FROM notes n LEFT JOIN folders f ON f.id = n.folder_id
                """

            )

        c.execute("DROP TABLE notes")
        c.execute("ALTER TABLE notes_new RENAME TO notes")
        c.execute("COMMIT")


def unique_is_global(conn: sqlite3.Connection, table: str, col: str) -> bool:
    # Heuristic: if there's a UNIQUE index only on (col), treat as global
    c = conn.cursor()
    c.execute(f"PRAGMA index_list({table})")
    for idx in c.fetchall():
        index_name = idx[1]
        c.execute(f"PRAGMA index_info({index_name})")
        cols = [r[2] for r in c.fetchall()]
        if cols == [col]:
            return True
    return False


init_db()


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)
    return wrapped


@app.context_processor
def inject_language():
    return {
        'current_language': get_current_language(),
        'current_theme': get_current_theme(),
        't': t,
        'current_user': {
            'id': session.get('user_id'),
            'username': session.get('username'),
        }
    }


# Auth routes
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""
        if not username or not password:
            flash("Please enter a username and password.", "error")
            return render_template("register.html")
        with get_conn() as conn:
            c = conn.cursor()
            try:
                c.execute(
                    "INSERT INTO users (username, password_hash, created_at) VALUES (?, ?, ?)",
                    (username, generate_password_hash(password), datetime.utcnow().isoformat()),
                )
                conn.commit()
            except sqlite3.IntegrityError:
                flash("Username already exists.", "error")
                return render_template("register.html")
            # Auto-login after register
            c.execute("SELECT id FROM users WHERE username = ?", (username,))
            user_id = c.fetchone()[0]
            session["user_id"] = user_id
            session["username"] = username
            return redirect(url_for("index"))
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""
        with get_conn() as conn:
            c = conn.cursor()
            c.execute("SELECT id, password_hash FROM users WHERE username = ?", (username,))
            row = c.fetchone()
            if not row or not check_password_hash(row[1], password):
                flash("Invalid username or password.", "error")
                return render_template("login.html")
            session["user_id"] = row[0]
            session["username"] = username
        next_url = request.args.get("next") or url_for("index")
        return redirect(next_url)
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/")
@login_required
def index():
    selected_folder = request.args.get("folder_id")
    user_id = session.get("user_id")

    # Separate sorting parameters for folders and notes
    folder_sort_by = request.args.get("folder_sort_by", "name")
    folder_sort_order = request.args.get("folder_sort_order", "asc")
    note_sort_by = request.args.get("sort_by", "name")
    note_sort_order = request.args.get("sort_order", "asc")
    search_query = request.args.get("search", "").strip()

    # Validate sort parameters
    if folder_sort_by not in ["name", "date"]:
        folder_sort_by = "name"
    if folder_sort_order not in ["asc", "desc"]:
        folder_sort_order = "asc"
    if note_sort_by not in ["name", "date"]:
        note_sort_by = "name"
    if note_sort_order not in ["asc", "desc"]:
        note_sort_order = "asc"

    with get_conn() as conn:
        c = conn.cursor()

        # Build folders query with search, sorting, and pinned status
        folders_query = "SELECT id, name, created_at, pinned FROM folders WHERE user_id = ?"
        folders_params = [user_id]

        if search_query:
            folders_query += " AND name LIKE ?"
            folders_params.append(f"%{search_query}%")

        # Order by pinned first, then by the selected sort criteria
        folders_query += " ORDER BY pinned DESC, "
        if folder_sort_by == "date":
            folders_query += "created_at " + ("ASC" if folder_sort_order == "asc" else "DESC")
        else:
            folders_query += "name " + ("ASC" if folder_sort_order == "asc" else "DESC")

        c.execute(folders_query, folders_params)
        folders = c.fetchall()

        # Build notes query with sorting and pinned status
        notes_params = [user_id]
        notes_query = "SELECT id, title, created_at, pinned FROM notes WHERE user_id = ?"
        if selected_folder:
            notes_query += " AND folder_id = ?"
            notes_params.append(selected_folder)

        # Order by pinned first, then by the selected sort criteria
        notes_query += " ORDER BY pinned DESC, "
        if note_sort_by == "date":
            notes_query += "created_at " + ("ASC" if note_sort_order == "asc" else "DESC")
        else:
            notes_query += "title " + ("ASC" if note_sort_order == "asc" else "DESC")

        c.execute(notes_query, notes_params)
        notes = c.fetchall()

    return render_template(
        "index.html",
        notes=notes,
        folders=folders,
        selected_folder=selected_folder,
        folder_sort_by=folder_sort_by,
        folder_sort_order=folder_sort_order,
        sort_by=note_sort_by,
        sort_order=note_sort_order,
        search_query=search_query
    )


@app.route("/add_folder", methods=["POST"])
@login_required
def add_folder():
    name = request.form["name"].strip()
    if not name:
        return redirect(url_for("index"))
    user_id = session.get("user_id")
    with get_conn() as conn:
        c = conn.cursor()
        try:
            c.execute("INSERT INTO folders (name, user_id) VALUES (?, ?)", (name, user_id))
            conn.commit()
        except sqlite3.IntegrityError:
            flash("Folder with this name already exists.", "error")
    return redirect(url_for("index"))


@app.route("/edit_folder/<int:folder_id>", methods=["GET", "POST"])
@login_required
def edit_folder(folder_id):
    user_id = session.get("user_id")
    with get_conn() as conn:
        c = conn.cursor()
        if request.method == "POST":
            new_name = request.form["name"].strip()
            if not new_name:
                return redirect(url_for("index"))
            try:
                c.execute("UPDATE folders SET name = ? WHERE id = ? AND user_id = ?", (new_name, folder_id, user_id))
                conn.commit()
            except sqlite3.IntegrityError:
                flash("Folder with this name already exists.", "error")
            return redirect(url_for("index"))
        else:
            c.execute("SELECT name FROM folders WHERE id = ? AND user_id = ?", (folder_id, user_id))
            folder = c.fetchone()
            if not folder:
                return redirect(url_for("index"))
    return render_template("edit_folder.html", folder=folder, folder_id=folder_id)


@app.route("/delete_folder/<int:folder_id>", methods=["POST"])
@login_required
def delete_folder(folder_id):
    """Delete a folder and all notes within it, cleaning up note files on disk."""
    user_id = session.get("user_id")
    with get_conn() as conn:
        c = conn.cursor()
        # Fetch filenames of notes in this folder belonging to user
        c.execute("SELECT filename FROM notes WHERE folder_id = ? AND user_id = ?", (folder_id, user_id))
        for (filename,) in c.fetchall():
            if filename:
                path = os.path.join(NOTES_DIR, filename)
                try:
                    if os.path.exists(path):
                        os.remove(path)
                except Exception:
                    # Ignore file errors to ensure DB cleanup continues
                    pass
        # Delete notes and then the folder (scoped by user)
        c.execute("DELETE FROM notes WHERE folder_id = ? AND user_id = ?", (folder_id, user_id))
        c.execute("DELETE FROM folders WHERE id = ? AND user_id = ?", (folder_id, user_id))
        conn.commit()
    return redirect(url_for("index"))


@app.route("/add_note", methods=["POST"])
@login_required
def add_note():
    title = (request.form.get("title") or "").strip()
    folder_id = request.form.get("folder_id")
    user_id = session.get("user_id")

    if not title or not folder_id:
        return redirect(url_for("index"))

    # Verify folder belongs to user
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("SELECT id FROM folders WHERE id = ? AND user_id = ?", (folder_id, user_id))
        if not c.fetchone():
            flash("Folder not found.", "error")
            return redirect(url_for("index"))

    safe_name = sanitize_filename(title)
    # Ensure unique filename per user by prefixing user id, but display title cleanly
    filename = f"u{user_id}_{safe_name}.md"
    filepath = os.path.join(NOTES_DIR, filename)

    # Pre-create empty file; remove if DB insert fails
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("")

    with get_conn() as conn:
        c = conn.cursor()
        try:
            c.execute(
                "INSERT INTO notes (title, filename, folder_id, user_id) VALUES (?, ?, ?, ?)",
                (title, filename, folder_id, user_id),
            )
            conn.commit()
        except sqlite3.IntegrityError:
            if os.path.exists(filepath):
                os.remove(filepath)
            flash("A note with this title already exists in this folder.", "error")

    return redirect(url_for("index", folder_id=folder_id))


@app.route("/edit/<int:note_id>", methods=["GET", "POST"])
@login_required
def edit_note(note_id):
    user_id = session.get("user_id")
    if request.method == "POST":
        new_title = request.form["title"].strip()
        new_content = request.form["content"]

        with get_conn() as conn:
            c = conn.cursor()
            c.execute("SELECT filename, folder_id FROM notes WHERE id = ? AND user_id = ?", (note_id, user_id))
            row = c.fetchone()
            if not row:
                return "Note not found", 404
            old_filename, folder_id = row

            safe_name = sanitize_filename(new_title)
            new_filename = f"u{user_id}_{safe_name}.md"

            try:
                c.execute("UPDATE notes SET title = ?, filename = ? WHERE id = ? AND user_id = ?", (new_title, new_filename, note_id, user_id))
                conn.commit()
            except sqlite3.IntegrityError:
                return "A note with this title already exists in this folder.", 400

            old_filepath = os.path.join(NOTES_DIR, old_filename)
            new_filepath = os.path.join(NOTES_DIR, new_filename)

            if old_filepath != new_filepath and os.path.exists(old_filepath):
                os.rename(old_filepath, new_filepath)

            with open(new_filepath, "w", encoding="utf-8") as f:
                f.write(new_content)

        return redirect(url_for("view_note", note_id=note_id))

    # GET Request
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("SELECT title, filename FROM notes WHERE id = ? AND user_id = ?", (note_id, user_id))
        note = c.fetchone()

    if not note:
        return "Note not found", 404

    filepath = os.path.join(NOTES_DIR, note[1])
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        content = ""

    return render_template(
        "edit.html", title=note[0], content=content, note_id=note_id
    )


@app.route("/delete/<int:note_id>", methods=["POST"])
@login_required
def delete_note(note_id):
    user_id = session.get("user_id")
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("SELECT filename FROM notes WHERE id = ? AND user_id = ?", (note_id, user_id))
        row = c.fetchone()
        if row:
            path = os.path.join(NOTES_DIR, row[0])
            if os.path.exists(path):
                os.remove(path)
            c.execute("DELETE FROM notes WHERE id = ? AND user_id = ?", (note_id, user_id))
            conn.commit()
    return redirect(url_for("index"))


@app.route("/upload_image", methods=["POST"])
@login_required
def upload_image():
    # Validate presence
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files["file"]
    if not file or file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    # Validate type by content-type and extension
    allowed_extensions = {"png", "jpg", "jpeg", "gif", "bmp", "webp", "svg"}
    filename = file.filename
    if "." not in filename:
        return jsonify({"error": "Invalid file format"}), 400
    ext = filename.rsplit(".", 1)[1].lower()
    if ext not in allowed_extensions or not (file.mimetype or "").startswith("image/"):
        return jsonify({"error": f"File type '{ext}' not allowed"}), 400

    # Ensure upload folder exists
    os.makedirs(app.config["UPLOAD_IMAGE_FOLDER"], exist_ok=True)

    # Generate unique filename to avoid collisions
    import uuid
    unique_name = f"{uuid.uuid4().hex}.{ext}"
    filepath = os.path.join(app.config["UPLOAD_IMAGE_FOLDER"], unique_name)

    try:
        file.save(filepath)
    except Exception as e:
        return jsonify({"error": f"Failed to save file: {e}"}), 500

    return jsonify({"url": f"/notes/images/{unique_name}"})


@app.route("/notes/images/<filename>")
@login_required
def get_uploaded_image(filename):
    return send_from_directory(app.config["UPLOAD_IMAGE_FOLDER"], filename)


@app.route("/save/<int:note_id>", methods=["POST"])
@login_required
def save_note(note_id):
    data = request.json
    new_content = data.get("content", "")
    user_id = session.get("user_id")
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("SELECT filename FROM notes WHERE id = ? AND user_id = ?", (note_id, user_id))
        note = c.fetchone()
        if note:
            filepath = os.path.join(NOTES_DIR, note[0])
            with open(filepath, "w") as f:
                f.write(new_content)
            return jsonify({"success": True})
        else:
            return jsonify({"success": False, "error": "Note not found"}), 404


@app.route("/note/<int:note_id>", methods=["GET"])
@login_required
def view_note(note_id):
    user_id = session.get("user_id")
    with get_conn() as conn:
        c = conn.cursor()
        c.execute(
            "SELECT title, filename, folder_id FROM notes WHERE id = ? AND user_id = ?",
            (note_id, user_id),
        )
        note = c.fetchone()

    if not note:
        return "Note not found", 404

    filepath = os.path.join(NOTES_DIR, note[1])
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        content = "Note content file not found."

    return render_template(
        "note.html", title=note[0], content=content, note_id=note_id, folder_id=note[2]
    )


@app.route("/get_notes", methods=["GET"])
@login_required
def get_notes():
    folder_id = request.args.get("folder_id")
    user_id = session.get("user_id")
    if not folder_id:
        return jsonify({"error": "Missing folder_id parameter"}), 400
    try:
        folder_id = int(folder_id)
    except ValueError:
        return jsonify({"error": "Invalid folder_id parameter"}), 400
    with get_conn() as conn:
        c = conn.cursor()
        c.execute(
            "SELECT id, title FROM notes WHERE folder_id = ? AND user_id = ?",
            (folder_id, user_id),
        )
        notes = [{"id": row[0], "title": row[1]} for row in c.fetchall()]
    return jsonify(notes)


# Share note functionality
@app.route("/share/<int:note_id>", methods=["POST"])
@login_required
def generate_share_code(note_id):
    """Generate a share code for a note"""
    user_id = session.get("user_id")

    with get_conn() as conn:
        c = conn.cursor()
        # Get note content
        c.execute("SELECT title, filename FROM notes WHERE id = ? AND user_id = ?", (note_id, user_id))
        note = c.fetchone()

        if not note:
            return jsonify({"success": False, "error": "Note not found"}), 404

        title, filename = note

        # Read note content
        filepath = os.path.join(NOTES_DIR, filename)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
        except FileNotFoundError:
            content = ""

        # Generate unique hex code
        share_code = secrets.token_hex(16)  # 32 character hex string

        # Check if share code already exists for this note
        c.execute("SELECT share_code FROM shared_notes WHERE note_id = ? AND original_user_id = ?", (note_id, user_id))
        existing = c.fetchone()

        if existing:
            # Update existing share
            c.execute("""
                UPDATE shared_notes 
                SET title = ?, content = ?, created_at = ?
                WHERE note_id = ? AND original_user_id = ?
            """, (title, content, datetime.utcnow().isoformat(), note_id, user_id))
            share_code = existing[0]
        else:
            # Create new share
            c.execute("""
                INSERT INTO shared_notes (share_code, note_id, original_user_id, title, content, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (share_code, note_id, user_id, title, content, datetime.utcnow().isoformat()))

        conn.commit()

        return jsonify({"success": True, "share_code": share_code})

@app.route("/import_note", methods=["POST"])
@login_required
def import_shared_note():
    """Import a note using share code"""
    share_code = request.form.get("share_code", "").strip()
    folder_id = request.form.get("folder_id")
    user_id = session.get("user_id")

    if not share_code:
        flash(t('invalid_share_code'), "error")
        return redirect(url_for("index"))

    # Validate hex format (32 characters)
    if not re.match(r'^[a-fA-F0-9]{32}$', share_code):
        flash(t('invalid_share_code'), "error")
        return redirect(url_for("index"))

    with get_conn() as conn:
        c = conn.cursor()

        # Find shared note
        c.execute("SELECT title, content, original_user_id FROM shared_notes WHERE share_code = ?", (share_code,))
        shared_note = c.fetchone()

        if not shared_note:
            flash(t('share_code_not_found'), "error")
            return redirect(url_for("index"))

        title, content, original_user_id = shared_note

        # Don't allow importing your own notes
        if original_user_id == user_id:
            flash("Bạn không thể nhập ghi chú của chính mình!", "error")
            return redirect(url_for("index"))

        # If no folder specified, use first available folder or create default
        if not folder_id:
            c.execute("SELECT id FROM folders WHERE user_id = ? ORDER BY id LIMIT 1", (user_id,))
            folder_result = c.fetchone()
            if folder_result:
                folder_id = folder_result[0]
            else:
                # Create default folder
                c.execute("INSERT INTO folders (name, user_id) VALUES (?, ?)", ("Imported", user_id))
                folder_id = c.lastrowid

        # Check if folder belongs to user
        c.execute("SELECT id FROM folders WHERE id = ? AND user_id = ?", (folder_id, user_id))
        if not c.fetchone():
            flash("Folder not found.", "error")
            return redirect(url_for("index"))

        # Create unique title if already exists
        original_title = title
        counter = 1
        while True:
            c.execute("SELECT id FROM notes WHERE title = ? AND folder_id = ? AND user_id = ?",
                     (title, folder_id, user_id))
            if not c.fetchone():
                break
            title = f"{original_title} ({counter})"
            counter += 1

        # Create file
        safe_name = sanitize_filename(title)
        filename = f"u{user_id}_{safe_name}.md"
        filepath = os.path.join(NOTES_DIR, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        # Insert note
        c.execute(
            "INSERT INTO notes (title, filename, folder_id, user_id) VALUES (?, ?, ?, ?)",
            (title, filename, folder_id, user_id),
        )

        conn.commit()

        flash(t('note_imported_successfully'), "success")
        return redirect(url_for("index", folder_id=folder_id))

# Simple helper to strip HTML to text and normalize paragraphs
def extract_plain_paragraphs(html: str):
    if not html:
        return []
    # Replace block-level tags with newlines to preserve structure
    block_tags = [
        'p', 'div', 'br', 'li', 'ul', 'ol', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        'tr', 'th', 'td', 'section', 'article'
    ]
    norm = html or ''
    # Convert <br> variants to newline
    norm = re.sub(r'<\s*br\s*/?>', '\n', norm, flags=re.I)
    # Convert block openings and closings to newlines
    for tag in block_tags:
        norm = re.sub(fr'<\s*/?{tag}[^>]*>', '\n', norm, flags=re.I)
    # Remove any remaining tags
    norm = re.sub(r'<[^>]+>', ' ', norm)
    # Unescape HTML entities
    norm = html_unescape(norm)
    # Collapse whitespace
    norm = re.sub(r'\s+',' ', norm)
    # Reintroduce paragraph boundaries by converting multiple spaces around newlines
    norm = re.sub(r'\s*\n\s*', '\n', norm)
    # Split into paragraphs by newline and filter
    paras = [p.strip() for p in norm.split('\n') if p and len(p.strip()) > 0]
    # Deduplicate consecutive duplicates
    deduped = []
    prev = None
    for p in paras:
        if p != prev:
            deduped.append(p)
            prev = p
    return deduped

# Basic QA over note paragraphs: token overlap + phrase matches
def answer_from_note(question: str, paragraphs: list[str]) -> dict:
    if not question or not paragraphs:
        return {"answer": "Mình chưa thấy nội dung phù hợp trong ghi chú.", "chunks": []}

    q = question.strip().lower()
    # Tiny bilingual stopword list (vi + en). Use literal set to avoid extra function call.
    stop = {
        'là','và','của','cho','các','một','những','được','trong','khi','với','từ','này','đó','đến','đi','ở','đã','sẽ','hay','hoặc','nếu','thì','vì','như','rằng',
        'the','and','of','to','in','a','an','is','are','was','were','for','on','at','as','by','or','if','then','that','this','these','those','be','been','it','its','into','about','over','under','can','could','should','would'
    }

    def tokenize(s: str):
        # Keep unicode word chars
        toks = re.findall(r'\w+', s.lower(), flags=re.UNICODE)
        return [t for t in toks if len(t) > 1 and t not in stop]

    q_tokens = tokenize(q)
    if not q_tokens:
        q_tokens = tokenize(re.sub(r'[^\w\s]', ' ', q))

    scored = []
    for idx, para in enumerate(paragraphs):
        p = para.lower()
        # Exact phrase occurrences
        phrase_hits = p.count(q)
        # Token overlap
        p_tokens = tokenize(p)
        overlap = 0
        if p_tokens and q_tokens:
            q_set = set(q_tokens)
            p_set = set(p_tokens)
            overlap = len(q_set & p_set)
        # Additional bonus if paragraph contains numbers/dates when question has numbers
        num_bonus = 1 if re.search(r'\d', q) and re.search(r'\d', p) else 0
        score = phrase_hits * 3 + overlap * 1.5 + num_bonus
        # Slight positional boost for earlier paragraphs
        score += max(0, 2.0 - (idx * 0.05))
        if score > 0:
            scored.append((score, idx, para))

    scored.sort(reverse=True)
    top = scored[:3]
    chunks = [para for (_, _, para) in top]

    if not chunks:
        return {"answer": "Mình chưa tìm thấy phần liên quan trong ghi chú. Hãy hỏi cụ thể hơn nhé!", "chunks": []}

    # Build an extractive answer
    answer_lines = [
        "Theo nội dung trong ghi chú, có các đoạn liên quan:",
    ]
    for i, ch in enumerate(chunks, 1):
        # Truncate very long paragraphs for display
        snippet = ch if len(ch) <= 600 else (ch[:580].rstrip() + '…')
        answer_lines.append(f"{i}. {snippet}")

    return {"answer": "\n".join(answer_lines), "chunks": chunks}


@app.route("/chat/<int:note_id>", methods=["POST"])
@login_required
def chat_note(note_id):
    user_id = session.get("user_id")
    data = request.get_json(silent=True) or {}
    message = (data.get("message") or "").strip()
    if not message:
        return jsonify({"error": "Missing message"}), 400

    # Verify ownership and load note content
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("SELECT title, filename FROM notes WHERE id = ? AND user_id = ?", (note_id, user_id))
        row = c.fetchone()
        if not row:
            return jsonify({"error": "Note not found"}), 404
        title, filename = row

    filepath = os.path.join(NOTES_DIR, filename)
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            html_content = f.read()
    except FileNotFoundError:
        html_content = ""

    # Prepare context and ask Gemini
    paragraphs = extract_plain_paragraphs(html_content)
    context = "\n".join(paragraphs) if paragraphs else ""

    # Always try Gemini first
    ai_text = ask_gemini(message, context)

    # Only fallback if Gemini explicitly says not configured
    if ai_text and ai_text.startswith("Chưa cấu hình GEMINI_API_KEY"):
        qa = answer_from_note(message, paragraphs)
        return jsonify({
            "title": title,
            "answer": qa.get("answer"),
            "chunks": qa.get("chunks", []),
        })

    return jsonify({
        "title": title,
        "answer": ai_text,
        "chunks": paragraphs[:3] if paragraphs else [],
    })


@app.route("/chat/general", methods=["POST"])
@login_required
def chat_general():
    """Chat tổng quát không cần ghi chú cụ thể"""
    data = request.get_json(silent=True) or {}
    message = (data.get("message") or "").strip()
    if not message:
        return jsonify({"error": "Missing message"}), 400

    # Chat tổng quát không có context ghi chú
    ai_text = ask_gemini(message, None)

    return jsonify({
        "answer": ai_text,
        "type": "general"
    })

@app.route('/set_reminder', methods=['POST'])
@login_required
def set_reminder():
    data = request.get_json()
    note_id = data.get('note_id')
    email = data.get('email')
    reminder_time_str = data.get('reminder_time')
    user_id = session.get('user_id') # Lấy user_id từ session

    if not all([note_id, email, reminder_time_str]):
        return jsonify({'status': 'error', 'message': 'Thiếu thông tin cần thiết.'}), 400

    try:
        reminder_time = datetime.fromisoformat(reminder_time_str)
        if reminder_time < datetime.now():
            return jsonify({'status': 'error', 'message': 'Không thể đặt lời nhắc trong quá khứ.'}), 400

        # Lấy thông tin ghi chú từ database
        conn = get_conn() # Dùng hàm get_conn() của bạn
        conn.row_factory = sqlite3.Row # Giúp truy cập cột bằng tên
        c = conn.cursor()
        note = c.execute('SELECT title, filename FROM notes WHERE id = ? AND user_id = ?',
                            (note_id, user_id)).fetchone()
        conn.close()

        if not note:
            return jsonify({'status': 'error', 'message': 'Không tìm thấy ghi chú hoặc không có quyền truy cập.'}), 404

        # Đọc nội dung từ file
        note_title = note['title']
        filepath = os.path.join(NOTES_DIR, note['filename'])
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                note_content = f.read()
        except FileNotFoundError:
            note_content = "(Nội dung không tìm thấy)"


        # Lên lịch gửi email
        job_id = f'reminder_{note_id}_{user_id}_{int(reminder_time.timestamp())}'
        scheduler.add_job(
            id=job_id,
            func=send_reminder_email,
            trigger='date',
            run_date=reminder_time,
            args=[app.app_context(), email, note_title, note_content],
            replace_existing=True
        )
        
        return jsonify({
            'status': 'success', 
            'message': f'Đã đặt lời nhắc thành công vào lúc {reminder_time.strftime("%H:%M ngày %d/%m/%Y")}'
        })

    except Exception as e:
        print(f"Lỗi khi đặt lời nhắc: {e}")
        return jsonify({'status': 'error', 'message': 'Có lỗi xảy ra phía máy chủ.'}), 500

@app.route("/pin_folder/<int:folder_id>", methods=["POST"])
@login_required
def pin_folder(folder_id):
    user_id = session.get("user_id")
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("UPDATE folders SET pinned = 1 WHERE id = ? AND user_id = ?", (folder_id, user_id))
        conn.commit()
    return jsonify({"success": True})

@app.route("/unpin_folder/<int:folder_id>", methods=["POST"])
@login_required
def unpin_folder(folder_id):
    user_id = session.get("user_id")
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("UPDATE folders SET pinned = 0 WHERE id = ? AND user_id = ?", (folder_id, user_id))
        conn.commit()
    return jsonify({"success": True})

@app.route("/pin_note/<int:note_id>", methods=["POST"])
@login_required
def pin_note(note_id):
    user_id = session.get("user_id")
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("UPDATE notes SET pinned = 1 WHERE id = ? AND user_id = ?", (note_id, user_id))
        conn.commit()
    return jsonify({"success": True})

@app.route("/unpin_note/<int:note_id>", methods=["POST"])
@login_required
def unpin_note(note_id):
    user_id = session.get("user_id")
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("UPDATE notes SET pinned = 0 WHERE id = ? AND user_id = ?", (note_id, user_id))
        conn.commit()
    return jsonify({"success": True})

# Ensure the Flask dev server starts when running `python app.py` directly
if __name__ == "__main__":
    # Debug prints to confirm the main guard is reached when running the script
    print("[app.py] __main__ reached. Flask app object created:", app)
    print("[app.py] Starting Flask development server on 127.0.0.1:5000 (debug=True, use_reloader=False)")
    # Bind to localhost for local development. Change to '0.0.0.0' to expose externally.
    app.run(host="127.0.0.1", port=5000, debug=True, use_reloader=False)
