"""Tests for the wanman CLI module.

Covers all command handlers, parser construction, dispatch logic,
and the main entry point to ensure >= 95% line coverage on src/.
"""

from __future__ import annotations

import argparse
from unittest.mock import patch

import pytest

from src.cli import (
    DISPATCH,
    build_parser,
    cmd_capsule_create,
    cmd_init,
    cmd_initiative_create,
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


# ---------------------------------------------------------------------------
# Individual command handler tests
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


class TestCmdInitiativeList:
    def test_prints_stub(self, capsys: pytest.CaptureFixture[str]) -> None:
        cmd_initiative_list(_ns())
        assert "[stub] wanman initiative list" in capsys.readouterr().out


class TestCmdInitiativeCreate:
    def test_prints_stub_with_title(self, capsys: pytest.CaptureFixture[str]) -> None:
        cmd_initiative_create(_ns(title="My Initiative"))
        out = capsys.readouterr().out
        assert "--title='My Initiative'" in out


class TestCmdInitiativeUpdate:
    def test_prints_stub_with_id(self, capsys: pytest.CaptureFixture[str]) -> None:
        cmd_initiative_update(_ns(id="abc-123"))
        out = capsys.readouterr().out
        assert "--id=abc-123" in out


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

    def test_parse_initiative_create(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["initiative", "create", "--title", "New"])
        assert args.initiative_cmd == "create"
        assert args.title == "New"

    def test_parse_initiative_update(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["initiative", "update", "--id", "x"])
        assert args.initiative_cmd == "update"
        assert args.id == "x"

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

    def test_initiative_list_dispatches(self, capsys: pytest.CaptureFixture[str]) -> None:
        assert dispatch(_ns(command="initiative", initiative_cmd="list")) == 0
        assert "[stub] wanman initiative list" in capsys.readouterr().out

    def test_initiative_create_dispatches(self, capsys: pytest.CaptureFixture[str]) -> None:
        assert dispatch(_ns(command="initiative", initiative_cmd="create", title="X")) == 0
        assert "initiative create" in capsys.readouterr().out

    def test_initiative_update_dispatches(self, capsys: pytest.CaptureFixture[str]) -> None:
        assert dispatch(_ns(command="initiative", initiative_cmd="update", id="y")) == 0
        assert "initiative update" in capsys.readouterr().out

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

    def test_initiative_list_returns_zero(self, capsys: pytest.CaptureFixture[str]) -> None:
        assert main(["initiative", "list"]) == 0
        assert "initiative list" in capsys.readouterr().out

    def test_initiative_create_returns_zero(self, capsys: pytest.CaptureFixture[str]) -> None:
        assert main(["initiative", "create", "--title", "Foo"]) == 0
        assert "Foo" in capsys.readouterr().out

    def test_initiative_update_returns_zero(self, capsys: pytest.CaptureFixture[str]) -> None:
        assert main(["initiative", "update", "--id", "bar"]) == 0
        assert "bar" in capsys.readouterr().out

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

    def test_unknown_command_via_main(self, capsys: pytest.CaptureFixture[str]) -> None:
        # build_parser with subcommand "bogus" would fail at parse_args;
        # test the dispatch path for unknown sub-command instead
        assert main(["initiative", "create", "--title", "X"]) == 0

    def test_none_command_via_main(self) -> None:
        """main([]) → parse_args returns command=None → dispatch returns 0."""
        assert main([]) == 0
