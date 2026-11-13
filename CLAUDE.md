# CLAUDE.md

This is a FORK of TheAlgorithms/Python, used for a class assignment (CS440).
Fork: `Andyhim/Python` (remote `origin`). Upstream: `TheAlgorithms/Python`
(remote `upstream`, fetch-only: its push URL is `DISABLED`).

Read @AGENTS.md and CONTRIBUTING.md too. The rules below are stricter and win
where they differ.

## Hard rules

- NEVER push to, open PRs on, or comment on TheAlgorithms/Python. All PRs target
  `Andyhim/Python`, base `master`. Every `gh pr`/`gh issue` write must pass
  `--repo Andyhim/Python` explicitly, and PR bodies go in `--body-file`.
  (Enforced by `.claude/hooks/fork_guard.py`. If it blocks you, fix the command;
  don't work around the guard.)
- One concern per PR. Change only the files the task needs; never edit README.md
  or DIRECTORY.md (auto-generated).
- Don't change code and tests in the same PR (PR template rule). Existing doctests
  are the regression guard for refactors.
- Preserve each file's existing line endings (some files are CRLF in the index;
  check with `git ls-files --eol <file>`). Never rewrite a whole file;
  `git diff --stat` must show only the lines you meant to change.
- When verifying a ty fix, ALSO check the rules still ignored in pyproject.toml
  (`--error <rule>`) on the changed file. A fix must not just move the error into
  a rule that's currently hidden.

## Code rules (from CONTRIBUTING.md)

- Type hints on all parameters and return values. Prefer precise types over Any.
- Doctests on every function, covering valid and erroneous input.
- snake_case for files, functions, variables. New files go in an existing directory.
- Must pass `ruff check` and `ruff format`. Must pass `pre-commit run`.
- ty is informational in CI, but for this task the target ty rule must report zero.

## Commands

- Tests for one file:  `uv run --python 3.15 --group test pytest --doctest-modules <file>`
- Lint/format:         `pre-commit run --files <files>`
- Type check (rule):   `uv run --python 3.15 --with ty ty check --error <rule> --output-format concise .`
- Type check (all):    `uv run --python 3.15 --with ty ty check --output-format concise .`
- Fork guard tests:    `uv run --python 3.15 --group test pytest .claude/hooks`

pytest is in the `test` dependency group, so pytest commands need `--group test`.

## Environment notes (Windows machine)

- `python`/`python3` here are Microsoft Store stubs that don't run anything. Use
  `uv run --python 3.15 ...` for project code, or `py -3` for a bare interpreter.
- pre-commit's `validate-filenames` hook runs `scripts/validate_filenames.py` via
  its `#!/usr/bin/env python3` shebang, so it fails here (exit 9009) unless a real
  `python3` comes first on PATH. Workaround: in your scratchpad, write a
  `python3.cmd` containing `@py -3 %*`, then prefix that directory to PATH for
  pre-commit and for `git commit` (whose git hook runs pre-commit):
  `PATH="<shim dir>:$PATH" pre-commit run --files ...`. Never skip the hook.
- `gh` lives at `C:\Program Files\GitHub CLI\gh.exe`; open a new shell if it isn't
  on PATH yet.
- ty 0.0.102 warns that four `[tool.ty]` rule names in pyproject.toml were renamed
  (for example `call-non-callable` became `not-callable`). The old names still work
  as `--error` flags. Those `renamed-rule` warnings point at pyproject.toml, not at
  the file you changed.

## Issue-linking convention

- #15187 and #15234 are TRACKING issues: write "Part of #15187", never
  "Fixes/Closes #15187" (that would close the tracker). This overrides the
  PR template's "Fixes #N" default.

## Workflow

1. `/start-issue <issue#> <slug>` to branch.
2. Make the minimal fix.
3. Delegate verification to the `check-runner` subagent.
4. Delegate review to the `contributing-reviewer` subagent.
5. `/open-fork-pr`.
