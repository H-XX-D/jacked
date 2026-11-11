"""Durable task status and tool receipts in a private SQLite database."""

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from uuid import uuid4


def timestamp():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class TaskStore:
    def __init__(self, directory):
        self.directory = directory
        directory.mkdir(mode=0o700, parents=True, exist_ok=True)
        self.db = sqlite3.connect(directory / "tasks.sqlite3", timeout=5)
        self.db.row_factory = sqlite3.Row
        self.db.executescript("""
            PRAGMA foreign_keys = ON;
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY, goal TEXT NOT NULL, config TEXT NOT NULL,
                status TEXT NOT NULL, attempt INTEGER NOT NULL DEFAULT 0,
                answer TEXT, error TEXT, updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS receipts (
                id INTEGER PRIMARY KEY, task_id TEXT NOT NULL REFERENCES tasks(id),
                attempt INTEGER NOT NULL, tool TEXT NOT NULL, request TEXT NOT NULL,
                status TEXT NOT NULL, result TEXT
            );
        """)

    @contextmanager
    def exclusive_run(self):
        # A separate lock DB lets receipts commit while holding the run lock.
        lock = sqlite3.connect(self.directory / "runner.sqlite3", timeout=0)
        try:
            try:
                lock.execute("BEGIN IMMEDIATE")
            except sqlite3.OperationalError as error:
                if error.sqlite_errorcode == sqlite3.SQLITE_BUSY:
                    raise RuntimeError("Another MATRIX task is running for this state directory.") from error
                raise
            yield
        finally:
            lock.close()

    def create(self, goal, config):
        task_id = uuid4().hex[:12]
        with self.db:
            self.db.execute(
                "INSERT INTO tasks (id, goal, config, status, updated_at) VALUES (?, ?, ?, 'ready', ?)",
                (task_id, goal, json.dumps(config), timestamp()),
            )
        return task_id

    def start(self, task_id):
        with self.db:
            self.db.execute(
                "UPDATE tasks SET status='running', attempt=attempt+1, answer=NULL, error=NULL, "
                "updated_at=? WHERE id=?",
                (timestamp(), task_id),
            )
        return self.get(task_id)["attempt"]

    def finish(self, task_id, status, *, answer=None, error=None):
        with self.db:
            self.db.execute(
                "UPDATE tasks SET status=?, answer=?, error=?, updated_at=? WHERE id=?",
                (status, answer, error, timestamp(), task_id),
            )

    def get(self, task_id):
        row = self.db.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
        if row is None:
            raise ValueError(f"Task not found: {task_id}")
        task = dict(row)
        task["config"] = json.loads(task["config"])
        return task

    def list(self):
        rows = self.db.execute(
            "SELECT id, status, attempt, substr(goal, 1, 160) AS goal, updated_at "
            "FROM tasks ORDER BY rowid DESC LIMIT 50"
        )
        return [dict(row) for row in rows]

    def recent_context(self, workspace, workspace_identity):
        rows = self.db.execute(
            "SELECT id, substr(goal, 1, 600) AS goal, substr(answer, 1, 850) AS answer "
            "FROM tasks WHERE status='completed' AND answer IS NOT NULL "
            "AND json_extract(config, '$.workspace') = ? "
            "AND json_extract(config, '$.workspace_identity') = json(?) "
            "ORDER BY rowid DESC LIMIT 4",
            (str(workspace), json.dumps(workspace_identity)),
        )
        return [dict(row) for row in reversed(list(rows))]

    def search_context(self, workspace, workspace_identity, query):
        rows = self.db.execute(
            "SELECT id, substr(goal, 1, 600) AS goal, substr(answer, 1, 850) AS answer "
            "FROM tasks WHERE status='completed' AND answer IS NOT NULL "
            "AND json_extract(config, '$.workspace') = ? "
            "AND json_extract(config, '$.workspace_identity') = json(?) "
            "AND instr(lower(goal || ' ' || answer), lower(?)) > 0 "
            "ORDER BY rowid DESC LIMIT 4",
            (str(workspace), json.dumps(workspace_identity), query),
        )
        return [dict(row) for row in rows]

    def begin_tool(self, task_id, attempt, name, request):
        with self.db:
            return self.db.execute(
                "INSERT INTO receipts (task_id, attempt, tool, request, status) VALUES (?, ?, ?, ?, 'started')",
                (task_id, attempt, name, json.dumps(request)),
            ).lastrowid

    def finish_tool(self, receipt_id, status, result):
        with self.db:
            self.db.execute(
                "UPDATE receipts SET status=?, result=? WHERE id=?",
                (status, json.dumps(result), receipt_id),
            )

    def receipts(self, task_id):
        rows = self.db.execute(
            "SELECT attempt, tool, request, status, result FROM receipts WHERE task_id=? ORDER BY id",
            (task_id,),
        )
        return [
            {**dict(row), "request": json.loads(row["request"]), "result": json.loads(row["result"] or "null")}
            for row in rows
        ]

    def close(self):
        self.db.close()
