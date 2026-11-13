#!/usr/bin/env python3
"""
PreToolUse hook: keep every push and PR on the fork, never upstream.

Claude Code pipes the pending tool call to stdin as JSON. For the Bash and
PowerShell tools the shell command is in ``tool_input.command``. Exit code 2
blocks the call and sends stderr back to Claude; exit code 0 lets it run.

The guard fails closed: a payload it can't read is blocked, not allowed.
"""

import json
import re
import sys

FORK = "Andyhim/Python"
UPSTREAM = "thealgorithms/python"

# gh subcommands that only read (or only touch the local checkout). Anything
# else under `gh pr` / `gh issue` writes to GitHub.
GH_READ_VERBS = {"checkout", "checks", "diff", "list", "status", "view"}
GH_WRITE_GROUPS = {"issue", "pr"}

# Split chained shell commands so each one is checked on its own.
SEGMENT_SPLIT = re.compile(r"&&|\|\||[;|\n]")
REPO_FLAG = re.compile(r"(?:--repo|-R)(?:=|\s+)[\"']?([^\s\"']+)")
GH_CALL = re.compile(r"\bgh(?:\.exe)?[\"']?\s+([a-z-]+)(?:\s+([a-z-]+))?")
GIT_PUSH = re.compile(r"\bgit\b.*\spush\b")  # the subcommand, not `--push`
GIT_PUSH_URL_CHANGE = re.compile(r"\bgit\b.*\bremote\b.*\bset-url\b.*--push\b")
GH_API_WRITE = re.compile(
    r"(?:-X|--method)(?:=|\s+)[\"']?(?:post|put|patch|delete)\b"
    r"|\s(?:-f|-F|--field|--raw-field|--input)\b",
    re.IGNORECASE,
)


def check_segment(segment: str) -> str | None:
    """
    Return a reason to block one shell command, or None to allow it.

    >>> check_segment("git push origin issue-15187-boruvka") is None
    True
    >>> check_segment("git push upstream master")
    'Blocked: pushing to upstream is forbidden.'
    >>> check_segment("gh issue view 15187 --repo TheAlgorithms/Python") is None
    True
    >>> check_segment("gh pr create --title x")
    'Blocked: gh pr create must pass --repo Andyhim/Python explicitly.'
    """
    lowered = segment.lower()
    # `--set-upstream` names a tracking option, not the upstream remote.
    names_upstream = UPSTREAM in lowered or bool(
        re.search(r"\bupstream\b", re.sub(r"--set-upstream(?:-to)?", "", lowered))
    )

    if GIT_PUSH.search(lowered) and names_upstream:
        return "Blocked: pushing to upstream is forbidden."

    if (
        GIT_PUSH_URL_CHANGE.search(lowered)
        and names_upstream
        and not lowered.rstrip().endswith(" disabled")
    ):
        return "Blocked: upstream's push URL must stay DISABLED."

    for match in GH_CALL.finditer(lowered):
        group, verb = match.group(1), match.group(2) or ""

        if group == "repo" and verb == "set-default" and UPSTREAM in lowered:
            return f"Blocked: the gh default repo must stay {FORK}."

        if group == "api":
            if "graphql" in lowered and "mutation" in lowered:
                return "Blocked: gh api GraphQL mutations can't be checked for target."
            if UPSTREAM in lowered and GH_API_WRITE.search(segment):
                return "Blocked: no gh api writes against TheAlgorithms/Python."
            continue

        if group not in GH_WRITE_GROUPS or verb in GH_READ_VERBS:
            continue

        # A write under `gh pr` / `gh issue`.
        if UPSTREAM in lowered:
            return (
                "Blocked: no gh writes that mention TheAlgorithms/Python. "
                "Put PR/issue text in --body-file."
            )
        repos = {repo.lower() for repo in REPO_FLAG.findall(segment)}
        if repos != {FORK.lower()}:
            return f"Blocked: gh {group} {verb} must pass --repo {FORK} explicitly."

    return None


def check(command: str) -> str | None:
    """
    Return a reason to block ``command``, or None to allow it.

    >>> check("git push origin fix-boruvka") is None
    True
    >>> check("git push upstream master")
    'Blocked: pushing to upstream is forbidden.'
    >>> check("gh pr create --title x") is not None
    True
    >>> check(f"gh pr create --repo {FORK} --base master --title x") is None
    True
    >>> check("gh issue comment 15187 -R TheAlgorithms/Python -b hi") is not None
    True
    >>> check("git fetch upstream && git push upstream HEAD") is not None
    True
    >>> check("") is None
    True
    """
    for segment in SEGMENT_SPLIT.split(command):
        if reason := check_segment(segment):
            return reason
    return None


def main() -> int:
    """Read the hook payload from stdin and return the process exit code."""
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        print("fork_guard: unreadable hook payload, blocking.", file=sys.stderr)
        return 2
    tool_input = payload.get("tool_input") if isinstance(payload, dict) else None
    command = tool_input.get("command", "") if isinstance(tool_input, dict) else ""
    if not isinstance(command, str):
        print("fork_guard: command is not a string, blocking.", file=sys.stderr)
        return 2
    if reason := check(command):
        print(reason, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
