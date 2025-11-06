import sqlite3
import os
from typing import List

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "notes.db")


def get_user_tables(conn: sqlite3.Connection) -> List[str]:
    cur = conn.cursor()
    # Lấy các bảng do người dùng tạo, bỏ qua bảng hệ thống sqlite_*
    cur.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type='table' AND name NOT LIKE 'sqlite_%';
    """)
    return [r[0] for r in cur.fetchall()]


def table_exists(conn: sqlite3.Connection, name: str) -> bool:
    cur = conn.cursor()
    cur.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=? LIMIT 1;",
        (name,),
    )
    return cur.fetchone() is not None


def quote_ident(name: str) -> str:
    # Escape dấu " theo chuẩn SQLite identifier quoting
    return f'"{name.replace("\"", "\"\"")}"'


def clear_db(db_path: str = DB_PATH) -> None:
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Không tìm thấy tệp cơ sở dữ liệu: {db_path}")

    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        # Tắt kiểm tra khóa ngoại để tránh lỗi phụ thuộc thứ tự xoá
        cur.execute("PRAGMA foreign_keys = OFF;")
        conn.commit()

        tables = get_user_tables(conn)
        print(f"Tìm thấy {len(tables)} bảng người dùng: {tables}")

        # Xoá dữ liệu từng bảng trong một transaction
        cur.execute("BEGIN;")
        for t in tables:
            qname = quote_ident(t)
            try:
                cur.execute(f"DELETE FROM {qname};")
                print(f"- Đã xoá dữ liệu bảng {t} (rows_changed={cur.rowcount})")
            except sqlite3.Error as e:
                print(f"! Lỗi khi xoá bảng {t}: {e}")
                raise

        # Reset AUTOINCREMENT nếu có dùng
        if table_exists(conn, "sqlite_sequence"):
            cur.execute("DELETE FROM sqlite_sequence;")
            print("- Đã reset AUTOINCREMENT (sqlite_sequence)")

        conn.commit()

        # Bật lại kiểm tra khoá ngoại
        cur.execute("PRAGMA foreign_keys = ON;")
        conn.commit()

        # Kiểm chứng: đếm số dòng mỗi bảng sau khi xoá
        empty_ok = True
        for t in tables:
            qname = quote_ident(t)
            try:
                cur.execute(f"SELECT COUNT(*) FROM {qname};")
                cnt = cur.fetchone()[0]
                print(f"Sau xoá: {t} -> {cnt} dòng")
                if cnt != 0:
                    empty_ok = False
            except sqlite3.Error as e:
                print(f"! Lỗi khi kiểm tra bảng {t}: {e}")
                empty_ok = False

        if empty_ok:
            print("Hoàn tất: Đã xoá sạch dữ liệu tất cả bảng người dùng (schema được giữ nguyên).")
        else:
            print("Cảnh báo: Một số bảng vẫn còn dữ liệu. Vui lòng kiểm tra log ở trên.")
    finally:
        conn.close()


if __name__ == "__main__":
    clear_db()

