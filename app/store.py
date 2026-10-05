import json
import sqlite3
from pathlib import Path


SCHEMA = """
CREATE TABLE IF NOT EXISTS emails (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  message_id TEXT NOT NULL UNIQUE,
  from_name TEXT NOT NULL,
  from_email TEXT NOT NULL,
  subject TEXT NOT NULL,
  body TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'processing',
  category TEXT,
  urgency TEXT,
  summary TEXT,
  requirements_json TEXT,
  draft TEXT,
  analysis_mode TEXT,
  error TEXT,
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  completed_at TEXT
);
CREATE TABLE IF NOT EXISTS events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  email_id INTEGER NOT NULL REFERENCES emails(id),
  stage TEXT NOT NULL,
  detail TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);
CREATE TABLE IF NOT EXISTS notifications (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  email_id INTEGER NOT NULL UNIQUE REFERENCES emails(id),
  channel TEXT NOT NULL DEFAULT 'simulation',
  recipient TEXT NOT NULL DEFAULT '销售工作台（模拟）',
  content TEXT NOT NULL,
  sent INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);
"""


class Store:
    def __init__(self, data_dir: Path):
        data_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = data_dir / "workflow.sqlite3"
        with self.connect() as db:
            db.executescript(SCHEMA)

    def connect(self):
        db = sqlite3.connect(self.db_path, timeout=15)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        db.execute("PRAGMA busy_timeout=15000")
        return db

    @staticmethod
    def as_dict(row):
        if row is None:
            return None
        result = dict(row)
        if "requirements_json" in result:
            result["requirements"] = json.loads(result.pop("requirements_json") or "[]")
        if "sent" in result:
            result["sent"] = bool(result["sent"])
        return result

    def claim(self, email: dict):
        with self.connect() as db:
            try:
                cur = db.execute(
                    "INSERT INTO emails(message_id,from_name,from_email,subject,body) VALUES (?,?,?,?,?)",
                    (email["message_id"], email["from_name"], email["from_email"], email["subject"], email["body"]),
                )
                email_id = cur.lastrowid
                db.execute("INSERT INTO events(email_id,stage,detail) VALUES (?,?,?)", (email_id, "received", "Webhook/演示样本已接收"))
                return email_id, False
            except sqlite3.IntegrityError:
                row = db.execute("SELECT * FROM emails WHERE message_id=?", (email["message_id"],)).fetchone()
                for key in ("from_name", "from_email", "subject", "body"):
                    if row[key] != email[key]:
                        raise ValueError("message_id 已存在，但邮件内容不同")
                return row["id"], True

    def add_event(self, email_id: int, stage: str, detail: str):
        with self.connect() as db:
            db.execute("INSERT INTO events(email_id,stage,detail) VALUES (?,?,?)", (email_id, stage, detail))

    def finish(self, email_id: int, analysis: dict, draft: str, mode: str):
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            db.execute(
                """UPDATE emails SET status='complete',category=?,urgency=?,summary=?,requirements_json=?,draft=?,analysis_mode=?,completed_at=strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE id=? AND status='processing'""",
                (analysis["category"], analysis["urgency"], analysis["summary"], json.dumps(analysis["requirements"], ensure_ascii=False), draft, mode, email_id),
            )
            db.execute("INSERT INTO events(email_id,stage,detail) VALUES (?,?,?)", (email_id, "classified", f"{analysis['category']} / {analysis['urgency']} / {mode}"))
            db.execute("INSERT INTO events(email_id,stage,detail) VALUES (?,?,?)", (email_id, "extracted", f"{len(analysis['requirements'])} 条需求；证据来自邮件原文"))
            db.execute("INSERT INTO events(email_id,stage,detail) VALUES (?,?,?)", (email_id, "drafted", "回复草稿已保存，等待人工审核"))
            content = f"新线索 #{email_id}｜{analysis['category']}｜{analysis['urgency']}｜{analysis['summary']}。请审核回复草稿。"
            db.execute("INSERT INTO notifications(email_id,content) VALUES (?,?)", (email_id, content))
            db.execute("INSERT INTO events(email_id,stage,detail) VALUES (?,?,?)", (email_id, "notified", "销售工作台已生成模拟通知；没有外发"))

    def fail(self, email_id: int, reason: str):
        with self.connect() as db:
            db.execute("UPDATE emails SET status='failed',error=? WHERE id=?", (reason[:300], email_id))
            db.execute("INSERT INTO events(email_id,stage,detail) VALUES (?,?,?)", (email_id, "failed", reason[:300]))

    def get(self, email_id: int):
        with self.connect() as db:
            row = db.execute("SELECT * FROM emails WHERE id=?", (email_id,)).fetchone()
            if not row:
                return None
            result = self.as_dict(row)
            result["events"] = [self.as_dict(r) for r in db.execute("SELECT stage,detail,created_at FROM events WHERE email_id=? ORDER BY id", (email_id,))]
            result["notification"] = self.as_dict(db.execute("SELECT channel,recipient,content,sent,created_at FROM notifications WHERE email_id=?", (email_id,)).fetchone())
            return result

    def list(self):
        with self.connect() as db:
            rows = db.execute("SELECT id,message_id,from_name,subject,status,category,urgency,summary,analysis_mode,created_at FROM emails ORDER BY id DESC LIMIT 100").fetchall()
            return [self.as_dict(row) for row in rows]

    def count(self):
        with self.connect() as db:
            return db.execute("SELECT count(*) FROM emails").fetchone()[0]
