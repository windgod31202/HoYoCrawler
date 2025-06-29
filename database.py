import sqlite3
import logging

logging.basicConfig(level=logging.INFO)

class DatabaseManager:
    def __init__(self, db_path="hoyolab_articles.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.create_table()

    def create_table(self):
        sql = """
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            url TEXT NOT NULL UNIQUE,
            timestamp TEXT NOT NULL
        )
        """
        self.conn.execute(sql)
        self.conn.commit()

    def fetch_existing_urls(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT url FROM articles")
        return set(row[0] for row in cursor.fetchall())

    def fetch_articles(self, keyword=""):
        cursor = self.conn.cursor()
        if keyword:
            cursor.execute(
                "SELECT title, url, timestamp FROM articles WHERE title LIKE ? ORDER BY timestamp DESC",
                (f"%{keyword}%",)
            )
        else:
            cursor.execute("SELECT title, url, timestamp FROM articles ORDER BY timestamp DESC")
        return cursor.fetchall()

    def delete_oldest_articles(self, n=5):
        cursor = self.conn.cursor()
        cursor.execute("SELECT id FROM articles ORDER BY timestamp ASC LIMIT ?", (n,))
        rows = cursor.fetchall()
        if not rows:
            return 0
        ids_to_delete = [row[0] for row in rows]
        cursor.executemany("DELETE FROM articles WHERE id = ?", [(i,) for i in ids_to_delete])
        self.conn.commit()
        return cursor.rowcount

    def save_article(self, title, url, timestamp):
        try:
            self.conn.execute(
                "INSERT OR IGNORE INTO articles (title, url, timestamp) VALUES (?, ?, ?)",
                (title, url, timestamp)
            )
            self.conn.commit()
            logging.info(f"[新增] {title}")
            return True
        except sqlite3.Error as e:
            logging.error(f"[錯誤] 資料庫寫入失敗: {e}")
            return False

    def close(self):
        self.conn.close()
