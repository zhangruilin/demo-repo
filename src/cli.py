"""Wanman CLI entry point.

Provides the ``wanman`` command-line interface for managing initiatives,
tasks, capsules, and agent communication.
"""

from __future__ import annotations

import argparse
import sys
import uuid
from typing import Any

from src.models import InitiativeStatus
from src.store import Store


# ---------------------------------------------------------------------------
# Store helper
# ---------------------------------------------------------------------------

_STORE_PATH: str | None = None


def _get_store() -> Store:
    """Return a Store instance using the configured database path."""
    return Store(_STORE_PATH if _STORE_PATH else ":memory:")


# ---------------------------------------------------------------------------
# Top-level command stubs
# ---------------------------------------------------------------------------


def cmd_init(args: argparse.Namespace) -> None:
    """Initialize wanman in the current repository."""
    print("[stub] wanman init -- not yet implemented")


def cmd_send(args: argparse.Namespace) -> None:
    """Send a message or event to an agent."""
    print(f"[stub] wanman send --target={args.target} -- not yet implemented")


def cmd_recv(args: argparse.Namespace) -> None:
    """Receive messages or events from an agent."""
    print("[stub] wanman recv -- not yet implemented")


# ---------------------------------------------------------------------------
# Initiative sub-commands
# ---------------------------------------------------------------------------


def cmd_initiative_list(args: argparse.Namespace) -> None:
    """List initiatives, optionally filtered by --status."""
    store = _get_store()
    try:
        status = getattr(args, "status", None)
        initiatives = store.list_initiatives(status=status)
        if not initiatives:
            print("No initiatives found.")
            return
        # Print as a formatted table
        header = f"{'ID':<12} {'STATUS':<12} {'PRI':<5} {'TITLE':<40} {'GOAL'}"
        print(header)
        print("-" * len(header))
        for init in initiatives:
            print(
                f"{init.id:<12} {init.status.value:<12} {init.priority:<5} "
                f"{init.title:<40} {init.goal}"
            )
    finally:
        store.close()


def cmd_initiative_create(args: argparse.Namespace) -> None:
    """Create a new initiative and print its ID."""
    store = _get_store()
    try:
        data: dict[str, Any] = {
            "id": uuid.uuid4().hex[:8],
            "title": args.title,
            "goal": args.goal,
            "priority": args.priority,
        }
        if args.status:
            data["status"] = args.status
        initiative = store.create_initiative(data)
        print(initiative.id)
    finally:
        store.close()


def cmd_initiative_get(args: argparse.Namespace) -> None:
    """Print details of an initiative by ID."""
    store = _get_store()
    try:
        initiative = store.get_initiative(args.id)
        if initiative is None:
            print(f"Initiative not found: {args.id}", file=sys.stderr)
            sys.exit(1)
        print(f"ID:         {initiative.id}")
        print(f"Title:      {initiative.title}")
        print(f"Goal:       {initiative.goal}")
        print(f"Summary:    {initiative.summary or '(none)'}")
        print(f"Priority:   {initiative.priority}")
        print(f"Status:     {initiative.status.value}")
        print(f"Sources:    {', '.join(initiative.sources) if initiative.sources else '(none)'}")
        print(f"Created By: {initiative.createdBy or '(unknown)'}")
        print(f"Created At: {initiative.createdAt}")
        print(f"Updated At: {initiative.updatedAt}")
    finally:
        store.close()


def cmd_initiative_update(args: argparse.Namespace) -> None:
    """Update an existing initiative."""
    store = _get_store()
    try:
        updates: dict[str, Any] = {}
        if args.title is not None:
            updates["title"] = args.title
        if args.goal is not None:
            updates["goal"] = args.goal
        if args.priority is not None:
            updates["priority"] = args.priority
        if args.status is not None:
            updates["status"] = args.status

        if not updates:
            print("No fields to update.", file=sys.stderr)
            sys.exit(1)

        changed = store.update_initiative(args.id, updates)
        if not changed:
            print(f"Initiative not found: {args.id}", file=sys.stderr)
            sys.exit(1)
        print(f"Initiative {args.id} updated.")
    finally:
        store.close()


# ---------------------------------------------------------------------------
# Task sub-commands
# ---------------------------------------------------------------------------


def cmd_task_list(args: argparse.Namespace) -> None:
    """List tasks."""
    print("[stub] wanman task list -- not yet implemented")


def cmd_task_create(args: argparse.Namespace) -> None:
    """Create a new task within an initiative."""
    print(
        f"[stub] wanman task create --initiative={args.initiative} "
        f"--title={args.title!r} -- not yet implemented"
    )


def cmd_task_assign(args: argparse.Namespace) -> None:
    """Assign a task to an agent."""
    print(f"[stub] wanman task assign --id={args.id} -- not yet implemented")


# ---------------------------------------------------------------------------
# Capsule sub-commands
# ---------------------------------------------------------------------------


def cmd_capsule_create(args: argparse.Namespace) -> None:
    """Create a capsule to bound changes for a task."""
    print(
        f"[stub] wanman capsule create --task={args.task} "
        f"--initiative={args.initiative} -- not yet implemented"
    )


# ---------------------------------------------------------------------------
# Argument parser construction
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    """Build and return the full CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="wanman",
        description="Wanman: multi-agent platform for autonomous repository takeover.",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # -- init ---------------------------------------------------------------
    subparsers.add_parser("init", help="Initialize wanman in the current repository")

    # -- send ---------------------------------------------------------------
    send_p = subparsers.add_parser("send", help="Send a message to an agent")
    send_p.add_argument("--target", required=True, help="Target agent name or id")
    send_p.add_argument("--message", default="", help="Message payload")

    # -- recv ---------------------------------------------------------------
    subparsers.add_parser("recv", help="Receive messages from an agent")

    # -- initiative ---------------------------------------------------------
    initiative_p = subparsers.add_parser("initiative", help="Manage initiatives")
    initiative_sub = initiative_p.add_subparsers(dest="initiative_cmd")

    # initiative list [--status STATUS]
    list_init = initiative_sub.add_parser("list", help="List initiatives")
    list_init.add_argument(
        "--status", default=None, choices=[s.value for s in InitiativeStatus],
        help="Filter by status",
    )

    # initiative create --title T --goal G [--priority P] [--status S]
    create_init = initiative_sub.add_parser("create", help="Create a new initiative")
    create_init.add_argument("--title", required=True, help="Initiative title")
    create_init.add_argument("--goal", required=True, help="Initiative goal")
    create_init.add_argument(
        "--priority", type=int, default=0, help="Numeric priority (default: 0)",
    )
    create_init.add_argument(
        "--status", default=None, choices=[s.value for s in InitiativeStatus],
        help="Initial status (default: active)",
    )

    # initiative get ID
    get_init = initiative_sub.add_parser("get", help="Get initiative details")
    get_init.add_argument("id", help="Initiative ID")

    # initiative update ID [--title/--goal/--priority/--status]
    update_init = initiative_sub.add_parser("update", help="Update an initiative")
    update_init.add_argument("id", help="Initiative ID")
    update_init.add_argument("--title", default=None, help="New title")
    update_init.add_argument("--goal", default=None, help="New goal")
    update_init.add_argument(
        "--priority", type=int, default=None, help="New priority",
    )
    update_init.add_argument(
        "--status", default=None, choices=[s.value for s in InitiativeStatus],
        help="New status",
    )

    # -- task ---------------------------------------------------------------
    task_p = subparsers.add_parser("task", help="Manage tasks")
    task_sub = task_p.add_subparsers(dest="task_cmd")

    task_sub.add_parser("list", help="List tasks")

    create_task = task_sub.add_parser("create", help="Create a new task")
    create_task.add_argument("--initiative", required=True, help="Parent initiative ID")
    create_task.add_argument("--title", required=True, help="Task title")
    create_task.add_argument("--path", default=None, help="File or directory scope")

    assign_task = task_sub.add_parser("assign", help="Assign a task")
    assign_task.add_argument("--id", required=True, help="Task ID")

    # -- capsule ------------------------------------------------------------
    capsule_p = subparsers.add_parser("capsule", help="Manage capsules")
    capsule_sub = capsule_p.add_subparsers(dest="capsule_cmd")

    create_cap = capsule_sub.add_parser("create", help="Create a capsule")
    create_cap.add_argument("--task", required=True, help="Task ID")
    create_cap.add_argument("--initiative", required=True, help="Initiative ID")
    create_cap.add_argument(
        "--paths", nargs="+", required=True, help="File paths to include"
    )

    return parser


# ---------------------------------------------------------------------------
# Command dispatch
# ---------------------------------------------------------------------------


DISPATCH: dict[str, dict[str, callable]] = {
    "init": {"__default__": cmd_init},
    "send": {"__default__": cmd_send},
    "recv": {"__default__": cmd_recv},
    "initiative": {
        "list": cmd_initiative_list,
        "create": cmd_initiative_create,
        "get": cmd_initiative_get,
        "update": cmd_initiative_update,
    },
    "task": {
        "list": cmd_task_list,
        "create": cmd_task_create,
        "assign": cmd_task_assign,
    },
    "capsule": {
        "create": cmd_capsule_create,
    },
}


def dispatch(args: argparse.Namespace) -> int:
    """Dispatch parsed arguments to the appropriate command handler."""
    command = args.command
    if command is None:
        return 0

    sub_table = DISPATCH.get(command)
    if sub_table is None:
        print(f"Unknown command: {command}", file=sys.stderr)
        return 1

    # Determine sub-command key: initiative_cmd / task_cmd / capsule_cmd
    sub_key = getattr(args, f"{command}_cmd", None) or "__default__"
    handler = sub_table.get(sub_key)
    if handler is None:
        print(f"Unknown sub-command: {command} {sub_key}", file=sys.stderr)
        return 1

    handler(args)
    return 0


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    """CLI entry point. Returns an exit code (0 = success)."""
    parser = build_parser()
    args = parser.parse_args(argv)
    return dispatch(args)


if __name__ == "__main__":
    sys.exit(main())
