"""
SQLite 数据库持久化模块

提供学生画像、学习路径、资源记录三张表的创建与增删改查接口。
数据库文件默认保存到 /home/hjj/桌面/A3-main/data/user_profiles/profiles.db
"""
from pathlib import Path
import sqlite3
import json
from typing import List, Optional, Dict, Any
import os


class Database:
    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            # 使用项目根目录下的 data/user_profiles/profiles.db
            project_root = Path(__file__).resolve().parent.parent.parent
            db_path = str(project_root / "data" / "user_profiles" / "profiles.db")
        self.db_path = str(Path(db_path).expanduser())
        parent = Path(self.db_path).parent
        parent.mkdir(parents=True, exist_ok=True)

    def _get_conn(self):
        conn = sqlite3.connect(self.db_path, timeout=30)
        conn.row_factory = sqlite3.Row
        return conn

    def create_tables(self):
        """创建三张表：student_profiles, learning_paths, resources"""
        with self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS student_profiles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT UNIQUE NOT NULL,
                    feat1 REAL,
                    feat2 REAL,
                    feat3 REAL,
                    feat4 REAL,
                    feat5 REAL,
                    feat6 REAL,
                    extra TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS learning_paths (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    step INTEGER NOT NULL,
                    progress REAL DEFAULT 0.0,
                    details TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, step)
                )
                """
            )

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS resources (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    resource_id TEXT UNIQUE,
                    resource_type TEXT,
                    content TEXT,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.commit()

    # ------------------- student_profiles CRUD -------------------
    def add_student_profile(self, user_id: str, features: List[float], extra: Optional[Dict[str, Any]] = None):
        if len(features) != 6:
            raise ValueError("features must be a list of 6 numeric values")
        extra_text = json.dumps(extra or {})
        with self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT OR REPLACE INTO student_profiles (user_id, feat1, feat2, feat3, feat4, feat5, feat6, extra)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (user_id, *features, extra_text),
            )
            conn.commit()
            return cur.lastrowid

    def get_student_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        with self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM student_profiles WHERE user_id = ?", (user_id,))
            row = cur.fetchone()
            if not row:
                return None
            return self._row_to_dict(row)

    def update_student_profile(self, user_id: str, features: Optional[List[float]] = None, extra: Optional[Dict[str, Any]] = None):
        if features is not None and len(features) != 6:
            raise ValueError("features must be a list of 6 numeric values")
        parts = []
        params = []
        if features is not None:
            parts += ["feat1 = ?", "feat2 = ?", "feat3 = ?", "feat4 = ?", "feat5 = ?", "feat6 = ?"]
            params += list(features)
        if extra is not None:
            parts.append("extra = ?")
            params.append(json.dumps(extra))
        if not parts:
            return 0
        params.append(user_id)
        sql = f"UPDATE student_profiles SET {', '.join(parts)} WHERE user_id = ?"
        with self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute(sql, tuple(params))
            conn.commit()
            return cur.rowcount

    def delete_student_profile(self, user_id: str):
        with self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM student_profiles WHERE user_id = ?", (user_id,))
            conn.commit()
            return cur.rowcount

    def list_student_profiles(self) -> List[Dict[str, Any]]:
        with self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM student_profiles")
            rows = cur.fetchall()
            return [self._row_to_dict(r) for r in rows]

    # ------------------- learning_paths CRUD -------------------
    def add_learning_step(self, user_id: str, step: int, progress: float = 0.0, details: str = ""):
        with self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT OR REPLACE INTO learning_paths (user_id, step, progress, details) VALUES (?, ?, ?, ?)",
                (user_id, step, progress, details),
            )
            conn.commit()
            return cur.lastrowid

    def get_learning_path(self, user_id: str) -> List[Dict[str, Any]]:
        with self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM learning_paths WHERE user_id = ? ORDER BY step", (user_id,))
            rows = cur.fetchall()
            return [self._row_to_dict(r) for r in rows]

    def update_learning_step(self, user_id: str, step: int, progress: Optional[float] = None, details: Optional[str] = None):
        parts = []
        params = []
        if progress is not None:
            parts.append("progress = ?")
            params.append(progress)
        if details is not None:
            parts.append("details = ?")
            params.append(details)
        if not parts:
            return 0
        params.extend([user_id, step])
        sql = f"UPDATE learning_paths SET {', '.join(parts)}, updated_at = CURRENT_TIMESTAMP WHERE user_id = ? AND step = ?"
        with self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute(sql, tuple(params))
            conn.commit()
            return cur.rowcount

    def delete_learning_step(self, user_id: str, step: int):
        with self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM learning_paths WHERE user_id = ? AND step = ?", (user_id, step))
            conn.commit()
            return cur.rowcount

    # ------------------- resources CRUD -------------------
    def add_resource(self, user_id: str, resource_id: str, resource_type: str, content: str, metadata: Optional[Dict[str, Any]] = None):
        meta_text = json.dumps(metadata or {})
        with self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT OR REPLACE INTO resources (user_id, resource_id, resource_type, content, metadata) VALUES (?, ?, ?, ?, ?)",
                (user_id, resource_id, resource_type, content, meta_text),
            )
            conn.commit()
            return cur.lastrowid

    def get_resource(self, resource_id: str) -> Optional[Dict[str, Any]]:
        with self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM resources WHERE resource_id = ?", (resource_id,))
            row = cur.fetchone()
            if not row:
                return None
            return self._row_to_dict(row)

    def list_resources(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._get_conn() as conn:
            cur = conn.cursor()
            if user_id is None:
                cur.execute("SELECT * FROM resources ORDER BY created_at")
            else:
                cur.execute("SELECT * FROM resources WHERE user_id = ? ORDER BY created_at", (user_id,))
            rows = cur.fetchall()
            return [self._row_to_dict(r) for r in rows]

    def update_resource(self, resource_id: str, content: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None, resource_type: Optional[str] = None):
        parts = []
        params = []
        if content is not None:
            parts.append("content = ?")
            params.append(content)
        if metadata is not None:
            parts.append("metadata = ?")
            params.append(json.dumps(metadata))
        if resource_type is not None:
            parts.append("resource_type = ?")
            params.append(resource_type)
        if not parts:
            return 0
        params.append(resource_id)
        sql = f"UPDATE resources SET {', '.join(parts)} WHERE resource_id = ?"
        with self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute(sql, tuple(params))
            conn.commit()
            return cur.rowcount

    def delete_resource(self, resource_id: str):
        with self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM resources WHERE resource_id = ?", (resource_id,))
            conn.commit()
            return cur.rowcount

    # ------------------- utils -------------------
    def _row_to_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        d = {k: row[k] for k in row.keys()}
        # try to decode JSON fields
        if d.get("extra"):
            try:
                d["extra"] = json.loads(d["extra"])
            except Exception:
                pass
        if d.get("metadata"):
            try:
                d["metadata"] = json.loads(d["metadata"])
            except Exception:
                pass
        return d
