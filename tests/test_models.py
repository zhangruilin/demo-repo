"""Tests for the data models in src.models."""

from __future__ import annotations

import pytest

from src.models import (
    Capsule,
    CapsuleStatus,
    Initiative,
    InitiativeStatus,
    Task,
    TaskStatus,
    _utcnow_iso,
)


# ---------------------------------------------------------------------------
# Enum tests
# ---------------------------------------------------------------------------


class TestInitiativeStatus:
    """Tests for InitiativeStatus enum."""

    def test_values(self) -> None:
        assert InitiativeStatus.ACTIVE.value == "active"
        assert InitiativeStatus.PAUSED.value == "paused"
        assert InitiativeStatus.COMPLETED.value == "completed"
        assert InitiativeStatus.ABANDONED.value == "abandoned"

    def test_member_count(self) -> None:
        assert len(InitiativeStatus) == 4

    def test_str_subclass(self) -> None:
        assert isinstance(InitiativeStatus.ACTIVE, str)


class TestTaskStatus:
    """Tests for TaskStatus enum."""

    def test_values(self) -> None:
        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.IN_PROGRESS.value == "in_progress"
        assert TaskStatus.DONE.value == "done"

    def test_member_count(self) -> None:
        assert len(TaskStatus) == 3

    def test_str_subclass(self) -> None:
        assert isinstance(TaskStatus.PENDING, str)


class TestCapsuleStatus:
    """Tests for CapsuleStatus enum."""

    def test_values(self) -> None:
        assert CapsuleStatus.OPEN.value == "open"
        assert CapsuleStatus.IN_REVIEW.value == "in_review"
        assert CapsuleStatus.MERGED.value == "merged"
        assert CapsuleStatus.ABANDONED.value == "abandoned"

    def test_member_count(self) -> None:
        assert len(CapsuleStatus) == 4

    def test_str_subclass(self) -> None:
        assert isinstance(CapsuleStatus.OPEN, str)


# ---------------------------------------------------------------------------
# Helper tests
# ---------------------------------------------------------------------------


class TestUtcnowIso:
    """Tests for the _utcnow_iso helper."""

    def test_returns_string(self) -> None:
        result = _utcnow_iso()
        assert isinstance(result, str)

    def test_contains_utc_indicator(self) -> None:
        result = _utcnow_iso()
        # ISO-8601 UTC offset is +00:00
        assert "+00:00" in result


# ---------------------------------------------------------------------------
# Initiative tests
# ---------------------------------------------------------------------------


class TestInitiative:
    """Tests for the Initiative dataclass."""

    def test_minimal_construction(self) -> None:
        init = Initiative(id="init-1", title="Test", goal="Do something")
        assert init.id == "init-1"
        assert init.title == "Test"
        assert init.goal == "Do something"
        assert init.summary == ""
        assert init.priority == 0
        assert init.status == InitiativeStatus.ACTIVE
        assert init.sources == []
        assert init.createdBy == ""
        assert isinstance(init.createdAt, str)
        assert isinstance(init.updatedAt, str)

    def test_full_construction(self) -> None:
        init = Initiative(
            id="init-2",
            title="Full",
            goal="Complete",
            summary="A full initiative",
            priority=1,
            status=InitiativeStatus.PAUSED,
            sources=["https://example.com"],
            createdBy="agent-1",
            createdAt="2024-01-01T00:00:00+00:00",
            updatedAt="2024-01-02T00:00:00+00:00",
        )
        assert init.summary == "A full initiative"
        assert init.priority == 1
        assert init.status == InitiativeStatus.PAUSED
        assert init.sources == ["https://example.com"]
        assert init.createdBy == "agent-1"

    def test_to_dict_minimal(self) -> None:
        init = Initiative(id="i1", title="T", goal="G")
        d = init.to_dict()
        assert d["id"] == "i1"
        assert d["title"] == "T"
        assert d["goal"] == "G"
        assert d["summary"] == ""
        assert d["priority"] == 0
        assert d["status"] == "active"
        assert d["sources"] == []
        assert d["createdBy"] == ""

    def test_to_dict_full(self) -> None:
        init = Initiative(
            id="i2",
            title="T2",
            goal="G2",
            summary="S",
            priority=3,
            status=InitiativeStatus.COMPLETED,
            sources=["s1", "s2"],
            createdBy="bot",
            createdAt="2024-06-01T00:00:00+00:00",
            updatedAt="2024-06-02T00:00:00+00:00",
        )
        d = init.to_dict()
        assert d["status"] == "completed"
        assert d["sources"] == ["s1", "s2"]
        assert d["createdBy"] == "bot"

    def test_to_dict_sources_mutation_safety(self) -> None:
        """Modifying the returned dict should not affect the model."""
        init = Initiative(id="i", title="T", goal="G", sources=["a"])
        d = init.to_dict()
        d["sources"].append("b")
        assert init.sources == ["a"]

    def test_from_dict_minimal(self) -> None:
        data = {"id": "i1", "title": "T", "goal": "G", "status": "active"}
        init = Initiative.from_dict(data)
        assert init.id == "i1"
        assert init.status == InitiativeStatus.ACTIVE
        assert init.summary == ""
        assert init.priority == 0
        assert init.sources == []
        assert init.createdBy == ""

    def test_from_dict_full(self) -> None:
        data = {
            "id": "i2",
            "title": "T2",
            "goal": "G2",
            "summary": "S",
            "priority": 2,
            "status": "abandoned",
            "sources": ["x"],
            "createdBy": "agent",
            "createdAt": "2024-01-01T00:00:00+00:00",
            "updatedAt": "2024-01-01T00:00:00+00:00",
        }
        init = Initiative.from_dict(data)
        assert init.status == InitiativeStatus.ABANDONED
        assert init.priority == 2
        assert init.sources == ["x"]

    def test_roundtrip(self) -> None:
        """Serialise then deserialise should reproduce the same model."""
        original = Initiative(
            id="rt-1",
            title="Roundtrip",
            goal="Test",
            summary="s",
            priority=5,
            status=InitiativeStatus.PAUSED,
            sources=["a", "b"],
            createdBy="me",
            createdAt="2024-03-01T00:00:00+00:00",
            updatedAt="2024-03-02T00:00:00+00:00",
        )
        restored = Initiative.from_dict(original.to_dict())
        assert restored == original

    def test_status_enum_in_from_dict(self) -> None:
        """Passing an InitiativeStatus enum directly should also work."""
        data = {"id": "i", "title": "T", "goal": "G", "status": InitiativeStatus.ACTIVE}
        init = Initiative.from_dict(data)
        assert init.status == InitiativeStatus.ACTIVE


# ---------------------------------------------------------------------------
# Task tests
# ---------------------------------------------------------------------------


class TestTask:
    """Tests for the Task dataclass."""

    def test_minimal_construction(self) -> None:
        task = Task(id="t1", title="Do thing")
        assert task.id == "t1"
        assert task.title == "Do thing"
        assert task.description == ""
        assert task.scope == []
        assert task.status == TaskStatus.PENDING
        assert task.priority == 0
        assert task.dependsOn == []
        assert task.initiativeId == ""
        assert task.capsuleId == ""
        assert task.subsystem == ""
        assert task.scopeType == ""
        assert task.result == ""
        assert isinstance(task.createdAt, str)
        assert isinstance(task.updatedAt, str)

    def test_full_construction(self) -> None:
        task = Task(
            id="t2",
            title="Full task",
            description="Do all the things",
            scope=["src/a.py", "src/b.py"],
            status=TaskStatus.IN_PROGRESS,
            priority=1,
            dependsOn=["t1"],
            initiativeId="init-1",
            capsuleId="cap-1",
            subsystem="auth",
            scopeType="file",
            result="done",
            createdAt="2024-01-01T00:00:00+00:00",
            updatedAt="2024-01-02T00:00:00+00:00",
        )
        assert task.description == "Do all the things"
        assert task.scope == ["src/a.py", "src/b.py"]
        assert task.status == TaskStatus.IN_PROGRESS
        assert task.dependsOn == ["t1"]
        assert task.subsystem == "auth"

    def test_to_dict_minimal(self) -> None:
        task = Task(id="t1", title="T")
        d = task.to_dict()
        assert d["id"] == "t1"
        assert d["title"] == "T"
        assert d["status"] == "pending"
        assert d["scope"] == []
        assert d["dependsOn"] == []

    def test_to_dict_full(self) -> None:
        task = Task(
            id="t2",
            title="T2",
            scope=["a"],
            status=TaskStatus.DONE,
            dependsOn=["t1"],
        )
        d = task.to_dict()
        assert d["status"] == "done"
        assert d["scope"] == ["a"]
        assert d["dependsOn"] == ["t1"]

    def test_to_dict_list_mutation_safety(self) -> None:
        task = Task(id="t", title="T", scope=["x"], dependsOn=["d"])
        d = task.to_dict()
        d["scope"].append("y")
        d["dependsOn"].append("e")
        assert task.scope == ["x"]
        assert task.dependsOn == ["d"]

    def test_from_dict_minimal(self) -> None:
        data = {"id": "t1", "title": "T", "status": "pending"}
        task = Task.from_dict(data)
        assert task.id == "t1"
        assert task.status == TaskStatus.PENDING
        assert task.description == ""
        assert task.scope == []

    def test_from_dict_full(self) -> None:
        data = {
            "id": "t2",
            "title": "T2",
            "description": "desc",
            "scope": ["a.py"],
            "status": "in_progress",
            "priority": 2,
            "dependsOn": ["t1"],
            "initiativeId": "init-1",
            "capsuleId": "cap-1",
            "subsystem": "core",
            "scopeType": "dir",
            "result": "ok",
            "createdAt": "2024-01-01T00:00:00+00:00",
            "updatedAt": "2024-01-01T00:00:00+00:00",
        }
        task = Task.from_dict(data)
        assert task.status == TaskStatus.IN_PROGRESS
        assert task.scope == ["a.py"]
        assert task.subsystem == "core"

    def test_roundtrip(self) -> None:
        original = Task(
            id="rt-t",
            title="RT",
            description="d",
            scope=["x"],
            status=TaskStatus.DONE,
            priority=1,
            dependsOn=["a"],
            initiativeId="i",
            capsuleId="c",
            subsystem="s",
            scopeType="file",
            result="r",
            createdAt="2024-01-01T00:00:00+00:00",
            updatedAt="2024-01-01T00:00:00+00:00",
        )
        restored = Task.from_dict(original.to_dict())
        assert restored == original


# ---------------------------------------------------------------------------
# Capsule tests
# ---------------------------------------------------------------------------


class TestCapsule:
    """Tests for the Capsule dataclass."""

    def test_minimal_construction(self) -> None:
        cap = Capsule(id="c1", goal="Fix bug")
        assert cap.id == "c1"
        assert cap.goal == "Fix bug"
        assert cap.ownerAgent == ""
        assert cap.branch == ""
        assert cap.baseCommit == ""
        assert cap.allowedPaths == []
        assert cap.acceptance == ""
        assert cap.reviewer == ""
        assert cap.status == CapsuleStatus.OPEN
        assert cap.initiativeId == ""
        assert cap.taskId == ""
        assert cap.subsystem == ""
        assert cap.scopeType == ""
        assert cap.blockedBy == []
        assert isinstance(cap.createdAt, str)
        assert isinstance(cap.updatedAt, str)

    def test_full_construction(self) -> None:
        cap = Capsule(
            id="c2",
            goal="Add feature",
            ownerAgent="dev-agent",
            branch="wanman/feat",
            baseCommit="abc123",
            allowedPaths=["src/feat.py"],
            acceptance="Tests pass",
            reviewer="cto-agent",
            status=CapsuleStatus.IN_REVIEW,
            initiativeId="init-1",
            taskId="t1",
            subsystem="feat",
            scopeType="file",
            blockedBy=["c0"],
            createdAt="2024-01-01T00:00:00+00:00",
            updatedAt="2024-01-02T00:00:00+00:00",
        )
        assert cap.ownerAgent == "dev-agent"
        assert cap.branch == "wanman/feat"
        assert cap.baseCommit == "abc123"
        assert cap.allowedPaths == ["src/feat.py"]
        assert cap.acceptance == "Tests pass"
        assert cap.reviewer == "cto-agent"
        assert cap.status == CapsuleStatus.IN_REVIEW
        assert cap.blockedBy == ["c0"]

    def test_to_dict_minimal(self) -> None:
        cap = Capsule(id="c1", goal="G")
        d = cap.to_dict()
        assert d["id"] == "c1"
        assert d["goal"] == "G"
        assert d["status"] == "open"
        assert d["allowedPaths"] == []
        assert d["blockedBy"] == []

    def test_to_dict_full(self) -> None:
        cap = Capsule(
            id="c2",
            goal="G2",
            allowedPaths=["a"],
            status=CapsuleStatus.MERGED,
            blockedBy=["c1"],
        )
        d = cap.to_dict()
        assert d["status"] == "merged"
        assert d["allowedPaths"] == ["a"]
        assert d["blockedBy"] == ["c1"]

    def test_to_dict_list_mutation_safety(self) -> None:
        cap = Capsule(id="c", goal="G", allowedPaths=["x"], blockedBy=["b"])
        d = cap.to_dict()
        d["allowedPaths"].append("y")
        d["blockedBy"].append("b2")
        assert cap.allowedPaths == ["x"]
        assert cap.blockedBy == ["b"]

    def test_from_dict_minimal(self) -> None:
        data = {"id": "c1", "goal": "G", "status": "open"}
        cap = Capsule.from_dict(data)
        assert cap.id == "c1"
        assert cap.status == CapsuleStatus.OPEN
        assert cap.ownerAgent == ""
        assert cap.allowedPaths == []

    def test_from_dict_full(self) -> None:
        data = {
            "id": "c2",
            "goal": "G2",
            "ownerAgent": "dev",
            "branch": "b",
            "baseCommit": "sha",
            "allowedPaths": ["p"],
            "acceptance": "ok",
            "reviewer": "r",
            "status": "abandoned",
            "initiativeId": "i",
            "taskId": "t",
            "subsystem": "s",
            "scopeType": "file",
            "blockedBy": ["c1"],
            "createdAt": "2024-01-01T00:00:00+00:00",
            "updatedAt": "2024-01-01T00:00:00+00:00",
        }
        cap = Capsule.from_dict(data)
        assert cap.status == CapsuleStatus.ABANDONED
        assert cap.ownerAgent == "dev"
        assert cap.blockedBy == ["c1"]

    def test_roundtrip(self) -> None:
        original = Capsule(
            id="rt-c",
            goal="RT",
            ownerAgent="a",
            branch="b",
            baseCommit="sha",
            allowedPaths=["p"],
            acceptance="ok",
            reviewer="r",
            status=CapsuleStatus.IN_REVIEW,
            initiativeId="i",
            taskId="t",
            subsystem="s",
            scopeType="dir",
            blockedBy=["x"],
            createdAt="2024-01-01T00:00:00+00:00",
            updatedAt="2024-01-01T00:00:00+00:00",
        )
        restored = Capsule.from_dict(original.to_dict())
        assert restored == original
