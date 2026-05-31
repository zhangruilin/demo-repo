"""Tests for the SQLite persistence layer (src.store)."""

from __future__ import annotations

import json
import sqlite3
import tempfile
from pathlib import Path

import pytest

from src.models import (
    Capsule,
    CapsuleStatus,
    Initiative,
    InitiativeStatus,
    Task,
    TaskStatus,
)
from src.store import Store


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def store() -> Store:
    """Return an in-memory Store that is closed after the test."""
    s = Store(":memory:")
    yield s
    s.close()


@pytest.fixture
def tmp_store(tmp_path: Path) -> Store:
    """Return a file-backed Store using a temporary directory."""
    db = tmp_path / "test.db"
    s = Store(db)
    yield s
    s.close()


# -- sample data helpers ---------------------------------------------------

def _initiative_data(**overrides: object) -> dict:
    """Return minimal initiative data, with optional overrides."""
    base = {
        "id": "init-001",
        "title": "First Initiative",
        "goal": "Ship v1",
        "summary": "MVP release",
        "priority": 1,
        "status": "active",
        "sources": ["https://github.com/example/repo/issues/1"],
        "createdBy": "agent-alpha",
    }
    base.update(overrides)
    return base


def _task_data(**overrides: object) -> dict:
    """Return minimal task data, with optional overrides."""
    base = {
        "id": "task-001",
        "title": "Implement store",
        "description": "Add SQLite persistence",
        "scope": ["src/store.py"],
        "status": "pending",
        "priority": 1,
        "dependsOn": [],
        "initiativeId": "init-001",
        "capsuleId": "",
        "subsystem": "core",
        "scopeType": "file",
    }
    base.update(overrides)
    return base


def _capsule_data(**overrides: object) -> dict:
    """Return minimal capsule data, with optional overrides."""
    base = {
        "id": "cap-001",
        "goal": "Implement store.py",
        "ownerAgent": "agent-beta",
        "branch": "wanman/add-store",
        "baseCommit": "abc1234",
        "allowedPaths": ["src/store.py", "tests/test_store.py"],
        "acceptance": "All tests pass",
        "reviewer": "agent-cto",
        "status": "open",
        "initiativeId": "init-001",
        "taskId": "task-001",
        "subsystem": "core",
        "scopeType": "file",
        "blockedBy": [],
    }
    base.update(overrides)
    return base


# ===========================================================================
# Initiative CRUD
# ===========================================================================

class TestInitiativeCRUD:
    """CRUD operations for initiatives."""

    def test_create_and_get(self, store: Store) -> None:
        data = _initiative_data()
        created = store.create_initiative(data)
        assert isinstance(created, Initiative)
        assert created.id == "init-001"
        assert created.title == "First Initiative"
        assert created.goal == "Ship v1"
        assert created.status == InitiativeStatus.ACTIVE
        assert created.sources == ["https://github.com/example/repo/issues/1"]

        fetched = store.get_initiative("init-001")
        assert fetched is not None
        assert fetched.id == created.id
        assert fetched.title == created.title

    def test_get_nonexistent_returns_none(self, store: Store) -> None:
        assert store.get_initiative("does-not-exist") is None

    def test_create_populates_defaults(self, store: Store) -> None:
        created = store.create_initiative({"id": "i2", "title": "T", "goal": "G"})
        assert created.summary == ""
        assert created.priority == 0
        assert created.status == InitiativeStatus.ACTIVE
        assert created.sources == []
        assert created.createdBy == ""

    def test_list_all(self, store: Store) -> None:
        store.create_initiative(_initiative_data(id="a", title="A", priority=2))
        store.create_initiative(_initiative_data(id="b", title="B", priority=1))
        results = store.list_initiatives()
        assert len(results) == 2
        # Ordered by priority (1 before 2)
        assert results[0].id == "b"
        assert results[1].id == "a"

    def test_list_filter_by_status(self, store: Store) -> None:
        store.create_initiative(_initiative_data(id="a", status="active"))
        store.create_initiative(_initiative_data(id="b", status="completed"))
        store.create_initiative(_initiative_data(id="c", status="active"))
        active = store.list_initiatives(status="active")
        assert len(active) == 2
        completed = store.list_initiatives(status="completed")
        assert len(completed) == 1

    def test_list_filter_by_enum_status(self, store: Store) -> None:
        store.create_initiative(_initiative_data(id="a", status="active"))
        store.create_initiative(_initiative_data(id="b", status="paused"))
        result = store.list_initiatives(status=InitiativeStatus.PAUSED)
        assert len(result) == 1
        assert result[0].status == InitiativeStatus.PAUSED

    def test_update_initiative(self, store: Store) -> None:
        store.create_initiative(_initiative_data())
        changed = store.update_initiative("init-001", {
            "title": "Updated Title",
            "status": "completed",
        })
        assert changed is True
        fetched = store.get_initiative("init-001")
        assert fetched is not None
        assert fetched.title == "Updated Title"
        assert fetched.status == InitiativeStatus.COMPLETED

    def test_update_nonexistent_returns_false(self, store: Store) -> None:
        assert store.update_initiative("nope", {"title": "x"}) is False

    def test_update_empty_data_returns_false(self, store: Store) -> None:
        store.create_initiative(_initiative_data())
        assert store.update_initiative("init-001", {}) is False

    def test_update_ignores_disallowed_columns(self, store: Store) -> None:
        store.create_initiative(_initiative_data())
        # 'id' and 'createdAt' are not updatable
        result = store.update_initiative("init-001", {
            "id": "hacked",
            "createdAt": "2000-01-01T00:00:00+00:00",
        })
        assert result is False
        # Original row is unchanged
        assert store.get_initiative("init-001") is not None
        assert store.get_initiative("hacked") is None

    def test_roundtrip_sources_list(self, store: Store) -> None:
        sources = ["https://a.com", "https://b.com"]
        store.create_initiative(_initiative_data(sources=sources))
        fetched = store.get_initiative("init-001")
        assert fetched is not None
        assert fetched.sources == sources

    def test_update_sources_list(self, store: Store) -> None:
        store.create_initiative(_initiative_data())
        store.update_initiative("init-001", {"sources": ["new-ref"]})
        fetched = store.get_initiative("init-001")
        assert fetched is not None
        assert fetched.sources == ["new-ref"]


# ===========================================================================
# Task CRUD
# ===========================================================================

class TestTaskCRUD:
    """CRUD operations for tasks."""

    def test_create_and_get(self, store: Store) -> None:
        created = store.create_task(_task_data())
        assert isinstance(created, Task)
        assert created.id == "task-001"
        assert created.title == "Implement store"
        assert created.status == TaskStatus.PENDING
        assert created.scope == ["src/store.py"]

        fetched = store.get_task("task-001")
        assert fetched is not None
        assert fetched.id == created.id

    def test_get_nonexistent_returns_none(self, store: Store) -> None:
        assert store.get_task("nope") is None

    def test_create_populates_defaults(self, store: Store) -> None:
        created = store.create_task({"id": "t2", "title": "T"})
        assert created.description == ""
        assert created.scope == []
        assert created.status == TaskStatus.PENDING
        assert created.initiativeId == ""

    def test_list_all(self, store: Store) -> None:
        store.create_task(_task_data(id="a", priority=2))
        store.create_task(_task_data(id="b", priority=1))
        results = store.list_tasks()
        assert len(results) == 2
        assert results[0].id == "b"

    def test_list_filter_by_status(self, store: Store) -> None:
        store.create_task(_task_data(id="a", status="pending"))
        store.create_task(_task_data(id="b", status="done"))
        store.create_task(_task_data(id="c", status="in_progress"))
        pending = store.list_tasks(status="pending")
        assert len(pending) == 1
        done = store.list_tasks(status="done")
        assert len(done) == 1

    def test_list_filter_by_enum_status(self, store: Store) -> None:
        store.create_task(_task_data(id="a", status="pending"))
        store.create_task(_task_data(id="b", status="in_progress"))
        result = store.list_tasks(status=TaskStatus.IN_PROGRESS)
        assert len(result) == 1
        assert result[0].status == TaskStatus.IN_PROGRESS

    def test_list_filter_by_initiative(self, store: Store) -> None:
        store.create_task(_task_data(id="a", initiativeId="init-1"))
        store.create_task(_task_data(id="b", initiativeId="init-2"))
        store.create_task(_task_data(id="c", initiativeId="init-1"))
        result = store.list_tasks(initiative_id="init-1")
        assert len(result) == 2

    def test_list_combined_filters(self, store: Store) -> None:
        store.create_task(_task_data(id="a", status="done", initiativeId="init-1"))
        store.create_task(_task_data(id="b", status="pending", initiativeId="init-1"))
        store.create_task(_task_data(id="c", status="done", initiativeId="init-2"))
        result = store.list_tasks(status="done", initiative_id="init-1")
        assert len(result) == 1
        assert result[0].id == "a"

    def test_update_task(self, store: Store) -> None:
        store.create_task(_task_data())
        changed = store.update_task("task-001", {
            "status": "done",
            "result": "Implemented successfully",
        })
        assert changed is True
        fetched = store.get_task("task-001")
        assert fetched is not None
        assert fetched.status == TaskStatus.DONE
        assert fetched.result == "Implemented successfully"

    def test_update_nonexistent_returns_false(self, store: Store) -> None:
        assert store.update_task("nope", {"title": "x"}) is False

    def test_roundtrip_scope_list(self, store: Store) -> None:
        scope = ["src/a.py", "src/b.py"]
        store.create_task(_task_data(scope=scope))
        fetched = store.get_task("task-001")
        assert fetched is not None
        assert fetched.scope == scope

    def test_roundtrip_depends_on_list(self, store: Store) -> None:
        store.create_task(_task_data(dependsOn=["task-000", "task-999"]))
        fetched = store.get_task("task-001")
        assert fetched is not None
        assert fetched.dependsOn == ["task-000", "task-999"]


# ===========================================================================
# Capsule CRUD
# ===========================================================================

class TestCapsuleCRUD:
    """CRUD operations for capsules."""

    def test_create_and_get(self, store: Store) -> None:
        created = store.create_capsule(_capsule_data())
        assert isinstance(created, Capsule)
        assert created.id == "cap-001"
        assert created.goal == "Implement store.py"
        assert created.status == CapsuleStatus.OPEN
        assert created.allowedPaths == ["src/store.py", "tests/test_store.py"]

        fetched = store.get_capsule("cap-001")
        assert fetched is not None
        assert fetched.id == created.id

    def test_get_nonexistent_returns_none(self, store: Store) -> None:
        assert store.get_capsule("nope") is None

    def test_create_populates_defaults(self, store: Store) -> None:
        created = store.create_capsule({"id": "c2", "goal": "G"})
        assert created.ownerAgent == ""
        assert created.branch == ""
        assert created.status == CapsuleStatus.OPEN
        assert created.allowedPaths == []
        assert created.blockedBy == []

    def test_list_all(self, store: Store) -> None:
        store.create_capsule(_capsule_data(id="a"))
        store.create_capsule(_capsule_data(id="b"))
        results = store.list_capsules()
        assert len(results) == 2

    def test_list_filter_by_status(self, store: Store) -> None:
        store.create_capsule(_capsule_data(id="a", status="open"))
        store.create_capsule(_capsule_data(id="b", status="merged"))
        open_caps = store.list_capsules(status="open")
        assert len(open_caps) == 1
        merged = store.list_capsules(status="merged")
        assert len(merged) == 1

    def test_list_filter_by_enum_status(self, store: Store) -> None:
        store.create_capsule(_capsule_data(id="a", status="open"))
        store.create_capsule(_capsule_data(id="b", status="in_review"))
        result = store.list_capsules(status=CapsuleStatus.IN_REVIEW)
        assert len(result) == 1
        assert result[0].status == CapsuleStatus.IN_REVIEW

    def test_list_filter_by_task(self, store: Store) -> None:
        store.create_capsule(_capsule_data(id="a", taskId="t1"))
        store.create_capsule(_capsule_data(id="b", taskId="t2"))
        store.create_capsule(_capsule_data(id="c", taskId="t1"))
        result = store.list_capsules(task_id="t1")
        assert len(result) == 2

    def test_list_filter_by_initiative(self, store: Store) -> None:
        store.create_capsule(_capsule_data(id="a", initiativeId="i1"))
        store.create_capsule(_capsule_data(id="b", initiativeId="i2"))
        result = store.list_capsules(initiative_id="i1")
        assert len(result) == 1

    def test_list_combined_filters(self, store: Store) -> None:
        store.create_capsule(_capsule_data(id="a", status="open", taskId="t1"))
        store.create_capsule(_capsule_data(id="b", status="merged", taskId="t1"))
        store.create_capsule(_capsule_data(id="c", status="open", taskId="t2"))
        result = store.list_capsules(status="open", task_id="t1")
        assert len(result) == 1
        assert result[0].id == "a"

    def test_update_capsule(self, store: Store) -> None:
        store.create_capsule(_capsule_data())
        changed = store.update_capsule("cap-001", {
            "status": "merged",
            "reviewer": "agent-cto-approved",
        })
        assert changed is True
        fetched = store.get_capsule("cap-001")
        assert fetched is not None
        assert fetched.status == CapsuleStatus.MERGED
        assert fetched.reviewer == "agent-cto-approved"

    def test_update_nonexistent_returns_false(self, store: Store) -> None:
        assert store.update_capsule("nope", {"goal": "x"}) is False

    def test_roundtrip_allowed_paths_list(self, store: Store) -> None:
        paths = ["src/a.py", "src/b.py", "tests/test_a.py"]
        store.create_capsule(_capsule_data(allowedPaths=paths))
        fetched = store.get_capsule("cap-001")
        assert fetched is not None
        assert fetched.allowedPaths == paths

    def test_roundtrip_blocked_by_list(self, store: Store) -> None:
        store.create_capsule(_capsule_data(blockedBy=["cap-999"]))
        fetched = store.get_capsule("cap-001")
        assert fetched is not None
        assert fetched.blockedBy == ["cap-999"]


# ===========================================================================
# File-backed persistence
# ===========================================================================

class TestFilePersistence:
    """Verify data survives across Store instances (file-backed)."""

    def test_data_persists_across_instances(self, tmp_store: Store) -> None:
        db_path = tmp_store._db_path
        tmp_store.create_initiative(_initiative_data())
        tmp_store.create_task(_task_data())
        tmp_store.create_capsule(_capsule_data())
        tmp_store.close()

        # Re-open the same file
        store2 = Store(db_path)
        try:
            assert store2.get_initiative("init-001") is not None
            assert store2.get_task("task-001") is not None
            assert store2.get_capsule("cap-001") is not None
        finally:
            store2.close()


# ===========================================================================
# Schema
# ===========================================================================

class TestSchema:
    """Verify that the schema is idempotent and the tables exist."""

    def test_schema_is_idempotent(self) -> None:
        """Opening the same Store twice should not raise."""
        store = Store(":memory:")
        store2 = Store(":memory:")
        store.close()
        store2.close()

    def test_tables_exist(self, store: Store) -> None:
        cur = store._conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        tables = [row[0] for row in cur.fetchall()]
        assert "initiatives" in tables
        assert "tasks" in tables
        assert "capsules" in tables

    def test_wal_mode_enabled(self, tmp_path: Path) -> None:
        # WAL mode cannot be set on :memory: databases, so use a file.
        db = tmp_path / "wal_test.db"
        s = Store(db)
        try:
            cur = s._conn.execute("PRAGMA journal_mode")
            mode = cur.fetchone()[0]
            assert mode.lower() == "wal"
        finally:
            s.close()

    def test_foreign_keys_enabled(self, store: Store) -> None:
        cur = store._conn.execute("PRAGMA foreign_keys")
        assert cur.fetchone()[0] == 1
