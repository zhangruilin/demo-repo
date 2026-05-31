"""SQLite persistence layer for Wanman domain objects.

Provides the ``Store`` class that wraps a SQLite database and exposes CRUD
operations for Initiatives, Tasks, and Capsules using the data models defined
in :mod:`src.models`.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from src.models import (
    Capsule,
    CapsuleStatus,
    Initiative,
    InitiativeStatus,
    Task,
    TaskStatus,
)

# ---------------------------------------------------------------------------
# SQL helpers
# ---------------------------------------------------------------------------

_SCHEMA_SQL = """\
CREATE TABLE IF NOT EXISTS initiatives (
    id          TEXT PRIMARY KEY,
    title       TEXT NOT NULL,
    goal        TEXT NOT NULL,
    summary     TEXT NOT NULL DEFAULT '',
    priority    INTEGER NOT NULL DEFAULT 0,
    status      TEXT NOT NULL DEFAULT 'active',
    sources     TEXT NOT NULL DEFAULT '[]',
    createdBy   TEXT NOT NULL DEFAULT '',
    createdAt   TEXT NOT NULL,
    updatedAt   TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS tasks (
    id            TEXT PRIMARY KEY,
    title         TEXT NOT NULL,
    description   TEXT NOT NULL DEFAULT '',
    scope         TEXT NOT NULL DEFAULT '[]',
    status        TEXT NOT NULL DEFAULT 'pending',
    priority      INTEGER NOT NULL DEFAULT 0,
    dependsOn     TEXT NOT NULL DEFAULT '[]',
    initiativeId  TEXT NOT NULL DEFAULT '',
    capsuleId     TEXT NOT NULL DEFAULT '',
    subsystem     TEXT NOT NULL DEFAULT '',
    scopeType     TEXT NOT NULL DEFAULT '',
    result        TEXT NOT NULL DEFAULT '',
    createdAt     TEXT NOT NULL,
    updatedAt     TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS capsules (
    id            TEXT PRIMARY KEY,
    goal          TEXT NOT NULL,
    ownerAgent    TEXT NOT NULL DEFAULT '',
    branch        TEXT NOT NULL DEFAULT '',
    baseCommit    TEXT NOT NULL DEFAULT '',
    allowedPaths  TEXT NOT NULL DEFAULT '[]',
    acceptance    TEXT NOT NULL DEFAULT '',
    reviewer      TEXT NOT NULL DEFAULT '',
    status        TEXT NOT NULL DEFAULT 'open',
    initiativeId  TEXT NOT NULL DEFAULT '',
    taskId        TEXT NOT NULL DEFAULT '',
    subsystem     TEXT NOT NULL DEFAULT '',
    scopeType     TEXT NOT NULL DEFAULT '',
    blockedBy     TEXT NOT NULL DEFAULT '[]',
    createdAt     TEXT NOT NULL,
    updatedAt     TEXT NOT NULL
);
"""


def _row_to_initiative(row: sqlite3.Row) -> Initiative:
    """Convert a database row to an :class:`Initiative`."""
    return Initiative(
        id=row["id"],
        title=row["title"],
        goal=row["goal"],
        summary=row["summary"],
        priority=row["priority"],
        status=InitiativeStatus(row["status"]),
        sources=json.loads(row["sources"]),
        createdBy=row["createdBy"],
        createdAt=row["createdAt"],
        updatedAt=row["updatedAt"],
    )


def _row_to_task(row: sqlite3.Row) -> Task:
    """Convert a database row to a :class:`Task`."""
    return Task(
        id=row["id"],
        title=row["title"],
        description=row["description"],
        scope=json.loads(row["scope"]),
        status=TaskStatus(row["status"]),
        priority=row["priority"],
        dependsOn=json.loads(row["dependsOn"]),
        initiativeId=row["initiativeId"],
        capsuleId=row["capsuleId"],
        subsystem=row["subsystem"],
        scopeType=row["scopeType"],
        result=row["result"],
        createdAt=row["createdAt"],
        updatedAt=row["updatedAt"],
    )


def _row_to_capsule(row: sqlite3.Row) -> Capsule:
    """Convert a database row to a :class:`Capsule`."""
    return Capsule(
        id=row["id"],
        goal=row["goal"],
        ownerAgent=row["ownerAgent"],
        branch=row["branch"],
        baseCommit=row["baseCommit"],
        allowedPaths=json.loads(row["allowedPaths"]),
        acceptance=row["acceptance"],
        reviewer=row["reviewer"],
        status=CapsuleStatus(row["status"]),
        initiativeId=row["initiativeId"],
        taskId=row["taskId"],
        subsystem=row["subsystem"],
        scopeType=row["scopeType"],
        blockedBy=json.loads(row["blockedBy"]),
        createdAt=row["createdAt"],
        updatedAt=row["updatedAt"],
    )


# ---------------------------------------------------------------------------
# Store
# ---------------------------------------------------------------------------

# Columns that are stored as JSON-encoded lists.
_LIST_COLUMNS = {
    "initiatives": {"sources"},
    "tasks": {"scope", "dependsOn"},
    "capsules": {"allowedPaths", "blockedBy"},
}

# Updatable fields per table (everything except id, createdAt).
_UPDATABLE = {
    "initiatives": {
        "title", "goal", "summary", "priority", "status",
        "sources", "createdBy", "updatedAt",
    },
    "tasks": {
        "title", "description", "scope", "status", "priority",
        "dependsOn", "initiativeId", "capsuleId", "subsystem",
        "scopeType", "result", "updatedAt",
    },
    "capsules": {
        "goal", "ownerAgent", "branch", "baseCommit", "allowedPaths",
        "acceptance", "reviewer", "status", "initiativeId", "taskId",
        "subsystem", "scopeType", "blockedBy", "updatedAt",
    },
}


class Store:
    """SQLite-backed persistence for Initiatives, Tasks, and Capsules.

    Parameters:
        db_path: Path to the SQLite database file.  Pass ``":memory:"`` for
            an in-memory database (useful for tests).
    """

    def __init__(self, db_path: str | Path = ":memory:") -> None:
        self._db_path = str(db_path)
        self._conn = sqlite3.connect(self._db_path)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA foreign_keys=ON")
        self._conn.executescript(_SCHEMA_SQL)
        self._conn.commit()

    # -- helpers -----------------------------------------------------------

    def close(self) -> None:
        """Close the underlying database connection."""
        self._conn.close()

    def _update(self, table: str, id: str, data: dict[str, Any]) -> bool:
        """Generic update helper.  Returns *True* if a row was changed."""
        allowed = _UPDATABLE[table]
        list_cols = _LIST_COLUMNS[table]
        set_clauses: list[str] = []
        params: list[Any] = []
        for key, value in data.items():
            if key not in allowed:
                continue
            if key in list_cols and isinstance(value, list):
                value = json.dumps(value)
            set_clauses.append(f"{key} = ?")
            params.append(value)
        if not set_clauses:
            return False
        params.append(id)
        sql = f"UPDATE {table} SET {', '.join(set_clauses)} WHERE id = ?"
        cur = self._conn.execute(sql, params)
        self._conn.commit()
        return cur.rowcount > 0

    # -- Initiatives -------------------------------------------------------

    def create_initiative(self, data: dict[str, Any]) -> Initiative:
        """Insert a new initiative and return it.

        *data* should contain at minimum ``id``, ``title``, and ``goal``.
        Missing optional fields are filled with model defaults.
        """
        data.setdefault("status", InitiativeStatus.ACTIVE.value)
        obj = Initiative.from_dict(data)
        self._conn.execute(
            """INSERT INTO initiatives
               (id, title, goal, summary, priority, status, sources,
                createdBy, createdAt, updatedAt)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                obj.id, obj.title, obj.goal, obj.summary, obj.priority,
                obj.status.value, json.dumps(obj.sources), obj.createdBy,
                obj.createdAt, obj.updatedAt,
            ),
        )
        self._conn.commit()
        return obj

    def get_initiative(self, id: str) -> Initiative | None:
        """Return an initiative by *id*, or ``None`` if not found."""
        cur = self._conn.execute(
            "SELECT * FROM initiatives WHERE id = ?", (id,),
        )
        row = cur.fetchone()
        return _row_to_initiative(row) if row else None

    def list_initiatives(
        self, status: str | InitiativeStatus | None = None,
    ) -> list[Initiative]:
        """Return all initiatives, optionally filtered by *status*."""
        if status is not None:
            status_val = status.value if isinstance(status, InitiativeStatus) else status
            cur = self._conn.execute(
                "SELECT * FROM initiatives WHERE status = ? ORDER BY priority, createdAt",
                (status_val,),
            )
        else:
            cur = self._conn.execute(
                "SELECT * FROM initiatives ORDER BY priority, createdAt",
            )
        return [_row_to_initiative(row) for row in cur.fetchall()]

    def update_initiative(self, id: str, data: dict[str, Any]) -> bool:
        """Update an initiative.  Returns *True* if the row existed."""
        return self._update("initiatives", id, data)

    # -- Tasks -------------------------------------------------------------

    def create_task(self, data: dict[str, Any]) -> Task:
        """Insert a new task and return it."""
        data.setdefault("status", TaskStatus.PENDING.value)
        obj = Task.from_dict(data)
        self._conn.execute(
            """INSERT INTO tasks
               (id, title, description, scope, status, priority,
                dependsOn, initiativeId, capsuleId, subsystem,
                scopeType, result, createdAt, updatedAt)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                obj.id, obj.title, obj.description,
                json.dumps(obj.scope), obj.status.value, obj.priority,
                json.dumps(obj.dependsOn), obj.initiativeId,
                obj.capsuleId, obj.subsystem, obj.scopeType,
                obj.result, obj.createdAt, obj.updatedAt,
            ),
        )
        self._conn.commit()
        return obj

    def get_task(self, id: str) -> Task | None:
        """Return a task by *id*, or ``None`` if not found."""
        cur = self._conn.execute("SELECT * FROM tasks WHERE id = ?", (id,))
        row = cur.fetchone()
        return _row_to_task(row) if row else None

    def list_tasks(
        self, status: str | TaskStatus | None = None,
        initiative_id: str | None = None,
    ) -> list[Task]:
        """Return tasks, optionally filtered by *status* and/or *initiative_id*."""
        clauses: list[str] = []
        params: list[Any] = []
        if status is not None:
            status_val = status.value if isinstance(status, TaskStatus) else status
            clauses.append("status = ?")
            params.append(status_val)
        if initiative_id is not None:
            clauses.append("initiativeId = ?")
            params.append(initiative_id)
        where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        cur = self._conn.execute(
            f"SELECT * FROM tasks{where} ORDER BY priority, createdAt", params,
        )
        return [_row_to_task(row) for row in cur.fetchall()]

    def update_task(self, id: str, data: dict[str, Any]) -> bool:
        """Update a task.  Returns *True* if the row existed."""
        return self._update("tasks", id, data)

    # -- Capsules ----------------------------------------------------------

    def create_capsule(self, data: dict[str, Any]) -> Capsule:
        """Insert a new capsule and return it."""
        data.setdefault("status", CapsuleStatus.OPEN.value)
        obj = Capsule.from_dict(data)
        self._conn.execute(
            """INSERT INTO capsules
               (id, goal, ownerAgent, branch, baseCommit, allowedPaths,
                acceptance, reviewer, status, initiativeId, taskId,
                subsystem, scopeType, blockedBy, createdAt, updatedAt)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                obj.id, obj.goal, obj.ownerAgent, obj.branch,
                obj.baseCommit, json.dumps(obj.allowedPaths),
                obj.acceptance, obj.reviewer, obj.status.value,
                obj.initiativeId, obj.taskId, obj.subsystem,
                obj.scopeType, json.dumps(obj.blockedBy),
                obj.createdAt, obj.updatedAt,
            ),
        )
        self._conn.commit()
        return obj

    def get_capsule(self, id: str) -> Capsule | None:
        """Return a capsule by *id*, or ``None`` if not found."""
        cur = self._conn.execute(
            "SELECT * FROM capsules WHERE id = ?", (id,),
        )
        row = cur.fetchone()
        return _row_to_capsule(row) if row else None

    def list_capsules(
        self, status: str | CapsuleStatus | None = None,
        task_id: str | None = None,
        initiative_id: str | None = None,
    ) -> list[Capsule]:
        """Return capsules, optionally filtered by status, task, or initiative."""
        clauses: list[str] = []
        params: list[Any] = []
        if status is not None:
            status_val = status.value if isinstance(status, CapsuleStatus) else status
            clauses.append("status = ?")
            params.append(status_val)
        if task_id is not None:
            clauses.append("taskId = ?")
            params.append(task_id)
        if initiative_id is not None:
            clauses.append("initiativeId = ?")
            params.append(initiative_id)
        where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        cur = self._conn.execute(
            f"SELECT * FROM capsules{where} ORDER BY createdAt", params,
        )
        return [_row_to_capsule(row) for row in cur.fetchall()]

    def update_capsule(self, id: str, data: dict[str, Any]) -> bool:
        """Update a capsule.  Returns *True* if the row existed."""
        return self._update("capsules", id, data)
