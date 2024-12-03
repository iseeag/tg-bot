import json
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional


class Database:
    def __init__(self, db_file: str = "tg_bots.db"):
        self.db_file = db_file
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            
            # Create bots table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS bots (
                    bot_id TEXT PRIMARY KEY,
                    token TEXT NOT NULL,
                    bot_handle TEXT NOT NULL,
                    config TEXT NOT NULL,
                    status TEXT DEFAULT 'stopped',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create chats table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS chats (
                    chat_id TEXT,
                    bot_id TEXT,
                    chat_name TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (chat_id, bot_id),
                    FOREIGN KEY (bot_id) REFERENCES bots(bot_id)
                )
            ''')
            
            # Create messages table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    message_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id TEXT,
                    bot_id TEXT,
                    message_text TEXT,
                    is_from_bot BOOLEAN,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (chat_id, bot_id) REFERENCES chats(chat_id, bot_id)
                )
            ''')
            
            conn.commit()

    def add_bot(self, bot_id: str, token: str, bot_handle: str, config: Dict) -> bool:
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO bots (bot_id, token, bot_handle, config) VALUES (?, ?, ?, ?)",
                    (bot_id, token, bot_handle, json.dumps(config))
                )
                conn.commit()
                return True
        except sqlite3.IntegrityError:
            return False

    def update_bot(self, bot_id: str, config: Dict) -> bool:
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE bots SET config = ? WHERE bot_id = ?",
                (json.dumps(config), bot_id)
            )
            return cursor.rowcount > 0

    def update_bot_status(self, bot_id: str, status: str) -> bool:
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE bots SET status = ? WHERE bot_id = ?",
                (status, bot_id)
            )
            return cursor.rowcount > 0

    def delete_bot(self, bot_id: str) -> bool:
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            # Delete all related messages and chats first
            cursor.execute("DELETE FROM messages WHERE bot_id = ?", (bot_id,))
            cursor.execute("DELETE FROM chats WHERE bot_id = ?", (bot_id,))
            cursor.execute("DELETE FROM bots WHERE bot_id = ?", (bot_id,))
            return cursor.rowcount > 0

    def get_bot(self, bot_id: str) -> Optional[Dict]:
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT bot_id, token, bot_handle, config, status FROM bots WHERE bot_id = ?",
                (bot_id,)
            )
            row = cursor.fetchone()
            if row:
                return {
                    "bot_id": row[0],
                    "token": row[1],
                    "bot_handle": row[2],
                    "config": json.loads(row[3]),
                    "status": row[4]
                }
            return None

    def get_all_bots(self) -> List[Dict]:
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT bot_id, token, bot_handle, config, status FROM bots")
            return [{
                "bot_id": row[0],
                "token": row[1],
                "bot_handle": row[2],
                "config": json.loads(row[3]),
                "status": row[4]
            } for row in cursor.fetchall()]

    def add_chat(self, chat_id: str, bot_id: str, chat_name: str) -> bool:
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO chats (chat_id, bot_id, chat_name) VALUES (?, ?, ?)",
                    (chat_id, bot_id, chat_name)
                )
                return True
        except sqlite3.IntegrityError:
            return False

    def get_chats(self, bot_id: str) -> List[Dict]:
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT chat_id, chat_name FROM chats WHERE bot_id = ?",
                (bot_id,)
            )
            return [{
                "chat_id": row[0],
                "chat_name": row[1]
            } for row in cursor.fetchall()]

    def add_message(self, chat_id: str, bot_id: str, message_text: str, is_from_bot: bool) -> bool:
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO messages (chat_id, bot_id, message_text, is_from_bot) VALUES (?, ?, ?, ?)",
                    (chat_id, bot_id, message_text, is_from_bot)
                )
                return True
        except sqlite3.IntegrityError:
            return False

    def get_chat_history(self, chat_id: str, bot_id: str) -> List[Dict]:
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT message_text, is_from_bot, timestamp 
                FROM messages 
                WHERE chat_id = ? AND bot_id = ?
                ORDER BY timestamp""",
                (chat_id, bot_id)
            )
            return [{
                "message": row[0],
                "is_from_bot": bool(row[1]),
                "timestamp": row[2]
            } for row in cursor.fetchall()]
