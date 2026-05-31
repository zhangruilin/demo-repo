"""Tests for the wanman CLI module.

Covers all command handlers, parser construction, dispatch logic,
and the main entry point to ensure >= 95% line coverage on src/.
"""

from __future__ import annotations

import argparse
import sys
from io import StringIO
from unittest.mock import patch

import pytest

from src.cli import (
    DISPATCH,
    build_parser,
    cmd_capsule_create,
    cmd_init,
    cmd_initiative_create,
    cmd_initiative_get,
    cmd_initiative_list,
    cmd_initiative_update,
    cmd_recv,
    cmd_send,
    cmd_task_assign,
    cmd_task_create,
    cmd_task_list,
    dispatch,
    main,
)
from src.models import InitiativeStatus
from src.store import Store


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _ns(**kwargs: object) -> argparse.Namespace:
    """Build an argparse.Namespace with sensible defaults."""
    defaults: dict[str, object] = {
        "command": None,
        "target": "",
        "message": "",
        "initiative_cmd": None,
        "title": "",
        "goal": "",
        "priority": 0,
        "status": None,
        "id": "",
        "task_cmd": None,
        "initiative": "",
        "path": None,
        "capsule_cmd": None,
        "task": "",
        "paths": [],
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def _run(argv: list[str], store_path: str = ":memory:") -> tuple[int, str, str]:
    """Run the CLI with *argv* and return (exit_code, stdout, stderr)."""
    with patch("src.cli._STORE_PATH", store_path):
        stdout, stderr = StringIO(), StringIO()
        old_out, old_err = sys.stdout, sys.stderr
        sys.stdout, sys.stderr = stdout, stderr
        try:
            code = main(argv)
        except SystemExit as exc:
            code = int(exc.code)
        finally:
            sys.stdout, sys.stderr = old_out, old_err
        return code, stdout.getvalue(), stderr.getvalue()


# ---------------------------------------------------------------------------
# Individual command handler tests (stubs)
# ---------------------------------------------------------------------------


class TestCmdInit:
    def test_prints_stub(self, capsys: pytest.CaptureFixture[str]) -> None:
        cmd_init(_ns())
        assert "[stub] wanman init" in capsys.readouterr().out


class TestCmdSend:
    def test_prints_stub_with_target(self, capsys: pytest.CaptureFixture[str]) -> None:
        cmd_send(_ns(target="cto"))
        out = capsys.readouterr().out
        assert "--target=cto" in out
        assert "[stub] wanman send" in out


class TestCmdRecv:
    def test_prints_stub(self, capsys: pytest.CaptureFixture[str]) -> None:
        cmd_recv(_ns())
        assert "[stub] wanman recv" in capsys.readouterr().out


class TestCmdTaskList:
    def test_prints_stub(self, capsys: pytest.CaptureFixture[str]) -> None:
        cmd_task_list(_ns())
        assert "[stub] wanman task list" in capsys.readouterr().out


class TestCmdTaskCreate:
    def test_prints_stub_with_fields(self, capsys: pytest.CaptureFixture[str]) -> None:
        cmd_task_create(_ns(initiative="init-1", title="Fix bug"))
        out = capsys.readouterr().out
        assert "--initiative=init-1" in out
        assert "--title='Fix bug'" in out


class TestCmdTaskAssign:
    def test_prints_stub_with_id(self, capsys: pytest.CaptureFixture[str]) -> None:
        cmd_task_assign(_ns(id="task-42"))
        out = capsys.readouterr().out
        assert "--id=task-42" in out


class TestCmdCapsuleCreate:
    def test_prints_stub_with_fields(self, capsys: pytest.CaptureFixture[str]) -> None:
        cmd_capsule_create(_ns(task="t-1", initiative="i-1"))
        out = capsys.readouterr().out
        assert "--task=t-1" in out
        assert "--initiative=i-1" in out


# ---------------------------------------------------------------------------
# Initiative command handler tests (real implementations)
# ---------------------------------------------------------------------------


class TestCmdInitiativeList:
    """Tests for the real initiative list command."""

    def test_empty_store(self, capsys: pytest.CaptureFixture[str]) -> None:  # noqa: F811

        cmd_initiative_list(_ns(status=None))
        assert "No initiatives found" in capsys.readouterr().out

    def test_lists_initiatives(self, tmp_path, capsys: pytest.CaptureFixture[str]) -> None:
        db = tmp_path / "test.db"
        store = Store(str(db))
        store.create_initiative({"id": "i1", "title": "First", "goal": "G1", "priority": 1})
        store.create_initiative({"id": "i2", "title": "Second", "goal": "G2", "priority": 2})
        store.close()

        with patch("src.cli._STORE_PATH", str(db)):
            cmd_initiative_list(_ns(status=None))
            out = capsys.readouterr().out
            assert "i1" in out
            assert "i2" in out
            assert "First" in out
            assert "Second" in out

    def test_filter_by_status(self, tmp_path, capsys: pytest.CaptureFixture[str]) -> None:
        db = tmp_path / "test.db"
        store = Store(str(db))
        store.create_initiative({"id": "i1", "title": "Active", "goal": "G", "status": "active"})
        store.create_initiative({"id": "i2", "title": "Done", "goal": "G", "status": "completed"})
        store.close()

        with patch("src.cli._STORE_PATH", str(db)):
            cmd_initiative_list(_ns(status="active"))
            out = capsys.readouterr().out
            assert "Active" in out
            assert "Done" not in out


class TestCmdInitiativeCreate:
    """Tests for the real initiative create command."""

    def test_create_basic(self, tmp_path, capsys: pytest.CaptureFixture[str]) -> None:
        db = tmp_path / "test.db"
        with patch("src.cli._STORE_PATH", str(db)):
            cmd_initiative_create(_ns(title="My Init", goal="Ship it", priority=0, status=None))
            out = capsys.readouterr().out
            created_id = out.strip()
            assert len(created_id) == 8

            store = Store(str(db))
            try:
                fetched = store.get_initiative(created_id)
                assert fetched is not None
                assert fetched.title == "My Init"
                assert fetched.goal == "Ship it"
                assert fetched.priority == 0
            finally:
                store.close()

    def test_create_with_priority(self, tmp_path, capsys: pytest.CaptureFixture[str]) -> None:
        db = tmp_path / "test.db"
        with patch("src.cli._STORE_PATH", str(db)):
            cmd_initiative_create(_ns(title="Pri", goal="G", priority=5, status=None))
            created_id = capsys.readouterr().out.strip()
            store = Store(str(db))
            try:
                fetched = store.get_initiative(created_id)
                assert fetched is not None
                assert fetched.priority == 5
            finally:
                store.close()

    def test_create_with_status(self, tmp_path, capsys: pytest.CaptureFixture[str]) -> None:
        db = tmp_path / "test.db"
        with patch("src.cli._STORE_PATH", str(db)):
            cmd_initiative_create(_ns(title="Paused", goal="G", priority=0, status="paused"))
            created_id = capsys.readouterr().out.strip()
            store = Store(str(db))
            try:
                fetched = store.get_initiative(created_id)
                assert fetched is not None
                assert fetched.status.value == "paused"
            finally:
                store.close()


class TestCmdInitiativeGet:
    """Tests for the real initiative get command."""

    def test_get_existing(self, tmp_path, capsys: pytest.CaptureFixture[str]) -> None:
        db = tmp_path / "test.db"
        store = Store(str(db))
        store.create_initiative({
            "id": "abc12345", "title": "Test", "goal": "Goal",
            "priority": 3, "status": "active", "summary": "Sum",
            "createdBy": "agent-dev",
        })
        store.close()

        with patch("src.cli._STORE_PATH", str(db)):
            cmd_initiative_get(_ns(id="abc12345"))
            out = capsys.readouterr().out
            assert "abc12345" in out
            assert "Test" in out
            assert "Goal" in out
            assert "Sum" in out
            assert "active" in out
            assert "agent-dev" in out

    def test_get_nonexistent_exits(self) -> None:
        with pytest.raises(SystemExit) as exc_info:
            with patch("src.cli._STORE_PATH", ":memory:"):
                cmd_initiative_get(_ns(id="nope"))
        assert exc_info.value.code == 1


class TestCmdInitiativeUpdate:
    """Tests for the real initiative update command."""

    def test_update_title(self, tmp_path, capsys: pytest.CaptureFixture[str]) -> None:
        db = tmp_path / "test.db"
        store = Store(str(db))
        store.create_initiative({"id": "u1", "title": "Old", "goal": "G"})
        store.close()

        with patch("src.cli._STORE_PATH", str(db)):
            cmd_initiative_update(_ns(id="u1", title="New", goal=None, priority=None, status=None))
            out = capsys.readouterr().out
            assert "updated" in out.lower()

        store = Store(str(db))
        try:
            fetched = store.get_initiative("u1")
            assert fetched is not None
            assert fetched.title == "New"
        finally:
            store.close()

    def test_update_status(self, tmp_path) -> None:
        db = tmp_path / "test.db"
        store = Store(str(db))
        store.create_initiative({"id": "u2", "title": "T", "goal": "G", "status": "active"})
        store.close()

        with patch("src.cli._STORE_PATH", str(db)):
            cmd_initiative_update(_ns(id="u2", title=None, goal=None, priority=None, status="completed"))

        store = Store(str(db))
        try:
            fetched = store.get_initiative("u2")
            assert fetched is not None
            assert fetched.status.value == "completed"
        finally:
            store.close()

    def test_update_goal_and_priority(self, tmp_path) -> None:
        db = tmp_path / "test.db"
        store = Store(str(db))
        store.create_initiative({"id": "u3", "title": "T", "goal": "Old", "priority": 1})
        store.close()

        with patch("src.cli._STORE_PATH", str(db)):
            cmd_initiative_update(_ns(id="u3", title=None, goal="New", priority=10, status=None))

        store = Store(str(db))
        try:
            fetched = store.get_initiative("u3")
            assert fetched is not None
            assert fetched.goal == "New"
            assert fetched.priority == 10
        finally:
            store.close()

    def test_update_nonexistent_exits(self) -> None:
        with pytest.raises(SystemExit) as exc_info:
            with patch("src.cli._STORE_PATH", ":memory:"):
                cmd_initiative_update(_ns(id="nope", title="X", goal=None, priority=None, status=None))
        assert exc_info.value.code == 1

    def test_update_no_fields_exits(self, tmp_path) -> None:
        db = tmp_path / "test.db"
        store = Store(str(db))
        store.create_initiative({"id": "u4", "title": "T", "goal": "G"})
        store.close()

        with pytest.raises(SystemExit) as exc_info:
            with patch("src.cli._STORE_PATH", str(db)):
                cmd_initiative_update(_ns(id="u4", title=None, goal=None, priority=None, status=None))
        assert exc_info.value.code == 1


# ---------------------------------------------------------------------------
# build_parser tests
# ---------------------------------------------------------------------------


class TestBuildParser:
    def test_returns_parser(self) -> None:
        parser = build_parser()
        assert isinstance(parser, argparse.ArgumentParser)
        assert parser.prog == "wanman"

    def test_parse_init(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["init"])
        assert args.command == "init"

    def test_parse_send(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["send", "--target", "agent-1"])
        assert args.command == "send"
        assert args.target == "agent-1"
        assert args.message == ""

    def test_parse_send_with_message(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["send", "--target", "agent-1", "--message", "hello"])
        assert args.message == "hello"

    def test_parse_recv(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["recv"])
        assert args.command == "recv"

    def test_parse_initiative_list(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["initiative", "list"])
        assert args.command == "initiative"
        assert args.initiative_cmd == "list"

    def test_parse_initiative_list_with_status(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["initiative", "list", "--status", "active"])
        assert args.status == "active"

    def test_parse_initiative_create(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["initiative", "create", "--title", "New", "--goal", "G"])
        assert args.initiative_cmd == "create"
        assert args.title == "New"
        assert args.goal == "G"
        assert args.priority == 0

    def test_parse_initiative_create_with_options(self) -> None:
        parser = build_parser()
        args = parser.parse_args([
            "initiative", "create",
            "--title", "T", "--goal", "G", "--priority", "5", "--status", "paused",
        ])
        assert args.priority == 5
        assert args.status == "paused"

    def test_parse_initiative_get(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["initiative", "get", "my-id"])
        assert args.initiative_cmd == "get"
        assert args.id == "my-id"

    def test_parse_initiative_update(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["initiative", "update", "x", "--title", "New"])
        assert args.initiative_cmd == "update"
        assert args.id == "x"
        assert args.title == "New"

    def test_parse_initiative_update_all_fields(self) -> None:
        parser = build_parser()
        args = parser.parse_args([
            "initiative", "update", "x",
            "--title", "T", "--goal", "G", "--priority", "3", "--status", "completed",
        ])
        assert args.title == "T"
        assert args.goal == "G"
        assert args.priority == 3
        assert args.status == "completed"

    def test_parse_task_list(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["task", "list"])
        assert args.command == "task"
        assert args.task_cmd == "list"

    def test_parse_task_create(self) -> None:
        parser = build_parser()
        args = parser.parse_args(
            ["task", "create", "--initiative", "i-1", "--title", "T"]
        )
        assert args.task_cmd == "create"
        assert args.initiative == "i-1"
        assert args.title == "T"

    def test_parse_task_create_with_path(self) -> None:
        parser = build_parser()
        args = parser.parse_args(
            ["task", "create", "--initiative", "i-1", "--title", "T", "--path", "src/"]
        )
        assert args.path == "src/"

    def test_parse_task_assign(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["task", "assign", "--id", "t-1"])
        assert args.task_cmd == "assign"
        assert args.id == "t-1"

    def test_parse_capsule_create(self) -> None:
        parser = build_parser()
        args = parser.parse_args(
            ["capsule", "create", "--task", "t-1", "--initiative", "i-1", "--paths", "a.py", "b.py"]
        )
        assert args.capsule_cmd == "create"
        assert args.task == "t-1"
        assert args.initiative == "i-1"
        assert args.paths == ["a.py", "b.py"]


# ---------------------------------------------------------------------------
# dispatch tests
# ---------------------------------------------------------------------------


class TestDispatch:
    def test_no_command_returns_zero(self) -> None:
        assert dispatch(_ns(command=None)) == 0

    def test_unknown_command_returns_one(self, capsys: pytest.CaptureFixture[str]) -> None:
        assert dispatch(_ns(command="bogus")) == 1
        assert "Unknown command: bogus" in capsys.readouterr().err

    def test_unknown_sub_command_returns_one(self, capsys: pytest.CaptureFixture[str]) -> None:
        ns = _ns(command="initiative", initiative_cmd="nonexistent")
        assert dispatch(ns) == 1
        assert "Unknown sub-command" in capsys.readouterr().err

    def test_init_dispatches(self, capsys: pytest.CaptureFixture[str]) -> None:
        assert dispatch(_ns(command="init")) == 0
        assert "[stub] wanman init" in capsys.readouterr().out

    def test_send_dispatches(self, capsys: pytest.CaptureFixture[str]) -> None:
        assert dispatch(_ns(command="send", target="a")) == 0
        assert "[stub] wanman send" in capsys.readouterr().out

    def test_recv_dispatches(self, capsys: pytest.CaptureFixture[str]) -> None:
        assert dispatch(_ns(command="recv")) == 0
        assert "[stub] wanman recv" in capsys.readouterr().out

    def test_task_list_dispatches(self, capsys: pytest.CaptureFixture[str]) -> None:
        assert dispatch(_ns(command="task", task_cmd="list")) == 0
        assert "[stub] wanman task list" in capsys.readouterr().out

    def test_task_create_dispatches(self, capsys: pytest.CaptureFixture[str]) -> None:
        assert dispatch(_ns(command="task", task_cmd="create", initiative="i", title="t")) == 0
        assert "task create" in capsys.readouterr().out

    def test_task_assign_dispatches(self, capsys: pytest.CaptureFixture[str]) -> None:
        assert dispatch(_ns(command="task", task_cmd="assign", id="z")) == 0
        assert "task assign" in capsys.readouterr().out

    def test_capsule_create_dispatches(self, capsys: pytest.CaptureFixture[str]) -> None:
        assert dispatch(_ns(command="capsule", capsule_cmd="create", task="t", initiative="i")) == 0
        assert "capsule create" in capsys.readouterr().out

    def test_dispatch_table_completeness(self) -> None:
        """All top-level commands in DISPATCH map to valid handlers."""
        expected_commands = {"init", "send", "recv", "initiative", "task", "capsule"}
        assert set(DISPATCH.keys()) == expected_commands


# ---------------------------------------------------------------------------
# main entry-point tests
# ---------------------------------------------------------------------------


class TestMain:
    def test_no_args_returns_zero(self) -> None:
        assert main([]) == 0

    def test_init_returns_zero(self, capsys: pytest.CaptureFixture[str]) -> None:
        assert main(["init"]) == 0
        assert "[stub] wanman init" in capsys.readouterr().out

    def test_send_returns_zero(self, capsys: pytest.CaptureFixture[str]) -> None:
        assert main(["send", "--target", "dev"]) == 0
        assert "--target=dev" in capsys.readouterr().out

    def test_send_with_message(self, capsys: pytest.CaptureFixture[str]) -> None:
        assert main(["send", "--target", "dev", "--message", "ping"]) == 0
        out = capsys.readouterr().out
        assert "--target=dev" in out

    def test_recv_returns_zero(self, capsys: pytest.CaptureFixture[str]) -> None:
        assert main(["recv"]) == 0

    def test_task_list_returns_zero(self, capsys: pytest.CaptureFixture[str]) -> None:
        assert main(["task", "list"]) == 0

    def test_task_create_returns_zero(self, capsys: pytest.CaptureFixture[str]) -> None:
        assert main(["task", "create", "--initiative", "i", "--title", "t"]) == 0
        out = capsys.readouterr().out
        assert "i" in out and "t" in out

    def test_task_assign_returns_zero(self, capsys: pytest.CaptureFixture[str]) -> None:
        assert main(["task", "assign", "--id", "q"]) == 0
        assert "q" in capsys.readouterr().out

    def test_capsule_create_returns_zero(self, capsys: pytest.CaptureFixture[str]) -> None:
        assert main(["capsule", "create", "--task", "t", "--initiative", "i", "--paths", "x.py"]) == 0
        out = capsys.readouterr().out
        assert "t" in out and "i" in out

    def test_capsule_create_multiple_paths(self, capsys: pytest.CaptureFixture[str]) -> None:
        assert main(["capsule", "create", "--task", "t", "--initiative", "i", "--paths", "a.py", "b.py"]) == 0

    def test_initiative_create_via_main(self, tmp_path) -> None:
        db = tmp_path / "test.db"
        code, out, _ = _run(
            ["initiative", "create", "--title", "Foo", "--goal", "Bar"],
            store_path=str(db),
        )
        assert code == 0
        assert len(out.strip()) == 8

    def test_initiative_get_via_main(self, tmp_path) -> None:
        db = tmp_path / "test.db"
        store = Store(str(db))
        store.create_initiative({"id": "test1234", "title": "T", "goal": "G"})
        store.close()

        code, out, _ = _run(["initiative", "get", "test1234"], store_path=str(db))
        assert code == 0
        assert "test1234" in out

    def test_initiative_list_via_main(self, tmp_path) -> None:
        db = tmp_path / "test.db"
        store = Store(str(db))
        store.create_initiative({"id": "i1", "title": "Init", "goal": "G"})
        store.close()

        code, out, _ = _run(["initiative", "list"], store_path=str(db))
        assert code == 0
        assert "Init" in out

    def test_initiative_update_via_main(self, tmp_path) -> None:
        db = tmp_path / "test.db"
        store = Store(str(db))
        store.create_initiative({"id": "u1", "title": "Old", "goal": "G"})
        store.close()

        code, out, _ = _run(
            ["initiative", "update", "u1", "--title", "New"],
            store_path=str(db),
        )
        assert code == 0
        assert "updated" in out.lower()

    def test_none_command_via_main(self) -> None:
        """main([]) → parse_args returns command=None → dispatch returns 0."""
        assert main([]) == 0
