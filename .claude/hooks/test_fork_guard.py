# ruff: noqa: INP001 -- .claude/hooks is a folder of hook scripts, not a package.
"""
Tests for fork_guard.py.

Run with: uv run --python 3.15 --group test pytest .claude/hooks
"""

import json
import shutil
import subprocess
import sys
from pathlib import Path

import fork_guard
import pytest

HOOKS_DIR = Path(__file__).resolve().parent
GUARD = HOOKS_DIR / "fork_guard.py"
LAUNCHER = HOOKS_DIR / "fork_guard.sh"
GH_EXE = '"C:\\Program Files\\GitHub CLI\\gh.exe"'

BLOCKED = [
    # Pushing upstream, by remote name or by URL.
    "git push upstream master",
    "git push upstream HEAD:master --force",
    "git -C repo push upstream my-branch",
    "git push https://github.com/TheAlgorithms/Python.git HEAD:master",
    "git fetch upstream && git push upstream HEAD",
    # Re-enabling upstream's push URL.
    "git remote set-url --push upstream https://github.com/TheAlgorithms/Python.git",
    # gh writes against upstream, however they are spelled.
    "gh pr create --repo TheAlgorithms/Python --title x",
    "gh pr create -R TheAlgorithms/Python --title x",
    "gh pr create --repo=TheAlgorithms/Python --title x",
    "gh issue comment 15187 -R TheAlgorithms/Python -b hi",
    "gh issue comment 15187 --repo thealgorithms/python --body hi",
    "gh pr comment https://github.com/TheAlgorithms/Python/pull/1 -b hi",
    "gh pr review 15568 --repo TheAlgorithms/Python --approve",
    "gh pr merge 1 --repo TheAlgorithms/Python",
    "gh issue create --repo TheAlgorithms/Python --title x",
    f"{GH_EXE} pr create --repo TheAlgorithms/Python --title x",
    "GH_REPO=TheAlgorithms/Python gh pr comment 1 -b hi",
    # gh writes with no explicit repo would use gh's default, which may be upstream.
    "gh pr create --title x --body-file body.md",
    "gh pr comment 1 -b hi",
    "gh issue edit 3 --add-label bug",
    # Two --repo flags: gh uses the last one, so any non-fork value blocks.
    "gh pr create --repo Andyhim/Python --repo TheAlgorithms/Python",
    # Fork repo but the body names upstream: use --body-file instead.
    'gh pr create --repo Andyhim/Python --body "see TheAlgorithms/Python#1"',
    # Pointing gh's default at upstream.
    "gh repo set-default TheAlgorithms/Python",
    # gh api writes against upstream, and GraphQL mutations (target unknowable).
    "gh api repos/TheAlgorithms/Python/issues/15187/comments -f body=hi",
    "gh api -X POST repos/TheAlgorithms/Python/pulls",
    "gh api --method=PATCH repos/TheAlgorithms/Python/issues/1",
    "gh api graphql -f query='mutation { addComment(input: {}) { clientMutationId } }'",
]

ALLOWED = [
    "",
    "git status",
    "git fetch upstream",
    "git merge --ff-only upstream/master",
    "git push origin master",
    "git push -u origin HEAD",
    (
        "git fetch upstream && git checkout master"
        " && git merge --ff-only upstream/master && git push origin master"
    ),
    "git push --set-upstream origin issue-15187-boruvka",
    "git remote set-url --push upstream DISABLED",
    "git remote -v",
    "gh issue view 15187 --repo TheAlgorithms/Python",
    "gh pr list --repo TheAlgorithms/Python --search boruvka",
    "gh pr view 15568 -R TheAlgorithms/Python --comments",
    "gh pr diff 15568 --repo TheAlgorithms/Python",
    "gh api repos/TheAlgorithms/Python/issues/15187",
    "gh pr create --repo Andyhim/Python --base master --title x --body-file b.md",
    "gh pr create -R Andyhim/Python --base master --title x --body-file b.md",
    "gh pr create --repo=andyhim/python --base master --title x --body-file b.md",
    f"{GH_EXE} pr create --repo Andyhim/Python --base master --body-file b.md",
    "gh pr comment 1 --repo Andyhim/Python --body-file note.md",
    "gh repo set-default Andyhim/Python",
    "echo hello | grep h",
]


@pytest.mark.parametrize("command", BLOCKED)
def test_blocked(command: str) -> None:
    assert fork_guard.check(command) is not None, command


@pytest.mark.parametrize("command", ALLOWED)
def test_allowed(command: str) -> None:
    assert fork_guard.check(command) is None, command


def run_guard(stdin: str, argv: list[str] | None = None) -> subprocess.CompletedProcess:
    """Run the hook the way Claude Code does: payload on stdin, check exit code."""
    return subprocess.run(  # noqa: S603 -- fixed argv, no shell
        argv or [sys.executable, str(GUARD)],
        input=stdin,
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )


def payload(command: str, tool: str = "Bash") -> str:
    return json.dumps({"tool_name": tool, "tool_input": {"command": command}})


@pytest.mark.parametrize("tool", ["Bash", "PowerShell"])
def test_subprocess_blocks_with_exit_2(tool: str) -> None:
    result = run_guard(payload("git push upstream master", tool))
    assert result.returncode == 2
    assert "Blocked" in result.stderr


def test_subprocess_allows_with_exit_0() -> None:
    result = run_guard(payload("git push -u origin HEAD"))
    assert result.returncode == 0
    assert result.stderr == ""


@pytest.mark.parametrize("stdin", ["not json", '{"tool_input": {"command": 5}}'])
def test_subprocess_fails_closed_on_bad_payload(stdin: str) -> None:
    assert run_guard(stdin).returncode == 2


def test_subprocess_missing_command_is_allowed() -> None:
    # Non-shell tool calls carry no command, so there is nothing to block.
    assert run_guard(json.dumps({"tool_input": {}})).returncode == 0


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash is not installed")
@pytest.mark.parametrize(
    ("command", "expected"),
    [("git push upstream master", 2), ("git push origin HEAD", 0)],
)
def test_launcher_script(command: str, expected: int) -> None:
    bash = shutil.which("bash") or "bash"
    result = run_guard(payload(command), [bash, LAUNCHER.as_posix()])
    assert result.returncode == expected, result.stderr
