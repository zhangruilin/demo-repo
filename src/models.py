"""Data models for Wanman initiative, task, and capsule management.

Provides Enum types and frozen dataclasses that represent the core domain
objects used throughout the wanman platform.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class InitiativeStatus(str, Enum):
    """Lifecycle states for an initiative."""

    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class TaskStatus(str, Enum):
    """Lifecycle states for a task."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    DONE = "done"


class CapsuleStatus(str, Enum):
    """Lifecycle states for a capsule."""

    OPEN = "open"
    IN_REVIEW = "in_review"
    MERGED = "merged"
    ABANDONED = "abandoned"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _utcnow_iso() -> str:
    """Return the current UTC time as an ISO-8601 string."""
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclass
class Initiative:
    """A high-level strategic objective that groups related tasks.

    Attributes:
        id: Unique identifier.
        title: Human-readable title.
        goal: Desired outcome or objective.
        summary: Brief description of the initiative.
        priority: Numeric priority (lower is higher priority).
        status: Current lifecycle status.
        sources: Origin references (e.g. issue URLs, docs).
        createdBy: Agent or user that created this initiative.
        createdAt: ISO-8601 creation timestamp.
        updatedAt: ISO-8601 last-updated timestamp.
    """

    id: str
    title: str
    goal: str
    summary: str = ""
    priority: int = 0
    status: InitiativeStatus = InitiativeStatus.ACTIVE
    sources: list[str] = field(default_factory=list)
    createdBy: str = ""
    createdAt: str = field(default_factory=_utcnow_iso)
    updatedAt: str = field(default_factory=_utcnow_iso)

    def to_dict(self) -> dict[str, Any]:
        """Serialise the initiative to a plain dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "goal": self.goal,
            "summary": self.summary,
            "priority": self.priority,
            "status": self.status.value,
            "sources": list(self.sources),
            "createdBy": self.createdBy,
            "createdAt": self.createdAt,
            "updatedAt": self.updatedAt,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Initiative:
        """Deserialise an initiative from a dictionary."""
        return cls(
            id=data["id"],
            title=data["title"],
            goal=data["goal"],
            summary=data.get("summary", ""),
            priority=data.get("priority", 0),
            status=InitiativeStatus(data["status"]),
            sources=list(data.get("sources", [])),
            createdBy=data.get("createdBy", ""),
            createdAt=data.get("createdAt", _utcnow_iso()),
            updatedAt=data.get("updatedAt", _utcnow_iso()),
        )


@dataclass
class Task:
    """A unit of work scoped to files or directories within an initiative.

    Attributes:
        id: Unique identifier.
        title: Human-readable title.
        description: Detailed description of the task.
        scope: File or directory paths that bound this task's work.
        status: Current lifecycle status.
        priority: Numeric priority (lower is higher priority).
        dependsOn: IDs of tasks that must complete before this one.
        initiativeId: Parent initiative ID.
        capsuleId: Associated capsule ID (set when work begins).
        subsystem: Logical subsystem or module name.
        scopeType: Type of scope (e.g. "file", "dir", "pattern").
        result: Outcome or output of the task.
        createdAt: ISO-8601 creation timestamp.
        updatedAt: ISO-8601 last-updated timestamp.
    """

    id: str
    title: str
    description: str = ""
    scope: list[str] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    priority: int = 0
    dependsOn: list[str] = field(default_factory=list)
    initiativeId: str = ""
    capsuleId: str = ""
    subsystem: str = ""
    scopeType: str = ""
    result: str = ""
    createdAt: str = field(default_factory=_utcnow_iso)
    updatedAt: str = field(default_factory=_utcnow_iso)

    def to_dict(self) -> dict[str, Any]:
        """Serialise the task to a plain dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "scope": list(self.scope),
            "status": self.status.value,
            "priority": self.priority,
            "dependsOn": list(self.dependsOn),
            "initiativeId": self.initiativeId,
            "capsuleId": self.capsuleId,
            "subsystem": self.subsystem,
            "scopeType": self.scopeType,
            "result": self.result,
            "createdAt": self.createdAt,
            "updatedAt": self.updatedAt,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Task:
        """Deserialise a task from a dictionary."""
        return cls(
            id=data["id"],
            title=data["title"],
            description=data.get("description", ""),
            scope=list(data.get("scope", [])),
            status=TaskStatus(data["status"]),
            priority=data.get("priority", 0),
            dependsOn=list(data.get("dependsOn", [])),
            initiativeId=data.get("initiativeId", ""),
            capsuleId=data.get("capsuleId", ""),
            subsystem=data.get("subsystem", ""),
            scopeType=data.get("scopeType", ""),
            result=data.get("result", ""),
            createdAt=data.get("createdAt", _utcnow_iso()),
            updatedAt=data.get("updatedAt", _utcnow_iso()),
        )


@dataclass
class Capsule:
    """A bounded change set tied to a task and branch.

    Attributes:
        id: Unique identifier.
        goal: What this capsule aims to achieve.
        ownerAgent: Agent responsible for the capsule.
        branch: Git branch name for the capsule's work.
        baseCommit: Starting commit SHA.
        allowedPaths: File paths the capsule may modify.
        acceptance: Criteria that must be met for the capsule to be accepted.
        reviewer: Agent or user assigned to review the capsule.
        status: Current lifecycle status.
        initiativeId: Parent initiative ID.
        taskId: Associated task ID.
        subsystem: Logical subsystem or module name.
        scopeType: Type of scope (e.g. "file", "dir", "pattern").
        blockedBy: IDs of capsules that block this one.
        createdAt: ISO-8601 creation timestamp.
        updatedAt: ISO-8601 last-updated timestamp.
    """

    id: str
    goal: str
    ownerAgent: str = ""
    branch: str = ""
    baseCommit: str = ""
    allowedPaths: list[str] = field(default_factory=list)
    acceptance: str = ""
    reviewer: str = ""
    status: CapsuleStatus = CapsuleStatus.OPEN
    initiativeId: str = ""
    taskId: str = ""
    subsystem: str = ""
    scopeType: str = ""
    blockedBy: list[str] = field(default_factory=list)
    createdAt: str = field(default_factory=_utcnow_iso)
    updatedAt: str = field(default_factory=_utcnow_iso)

    def to_dict(self) -> dict[str, Any]:
        """Serialise the capsule to a plain dictionary."""
        return {
            "id": self.id,
            "goal": self.goal,
            "ownerAgent": self.ownerAgent,
            "branch": self.branch,
            "baseCommit": self.baseCommit,
            "allowedPaths": list(self.allowedPaths),
            "acceptance": self.acceptance,
            "reviewer": self.reviewer,
            "status": self.status.value,
            "initiativeId": self.initiativeId,
            "taskId": self.taskId,
            "subsystem": self.subsystem,
            "scopeType": self.scopeType,
            "blockedBy": list(self.blockedBy),
            "createdAt": self.createdAt,
            "updatedAt": self.updatedAt,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Capsule:
        """Deserialise a capsule from a dictionary."""
        return cls(
            id=data["id"],
            goal=data["goal"],
            ownerAgent=data.get("ownerAgent", ""),
            branch=data.get("branch", ""),
            baseCommit=data.get("baseCommit", ""),
            allowedPaths=list(data.get("allowedPaths", [])),
            acceptance=data.get("acceptance", ""),
            reviewer=data.get("reviewer", ""),
            status=CapsuleStatus(data["status"]),
            initiativeId=data.get("initiativeId", ""),
            taskId=data.get("taskId", ""),
            subsystem=data.get("subsystem", ""),
            scopeType=data.get("scopeType", ""),
            blockedBy=list(data.get("blockedBy", [])),
            createdAt=data.get("createdAt", _utcnow_iso()),
            updatedAt=data.get("updatedAt", _utcnow_iso()),
        )
