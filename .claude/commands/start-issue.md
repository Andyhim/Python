---
description: "Start work on an issue in the fork. Usage: /start-issue <issue#> <short-slug>"
argument-hint: <issue#> <short-slug>
---

Arguments: `$ARGUMENTS`. The first word is the issue number (`N`), the
second is a short kebab-case slug (`SLUG`).

1. Sync the fork's master with upstream (upstream is fetch-only):
   `git fetch upstream && git checkout master && git merge --ff-only upstream/master && git push origin master`.
   If the fast-forward fails, stop and report it; don't merge or rebase.
2. `git checkout -b issue-N-SLUG`.
3. Read the issue, read-only: `gh issue view N --repo TheAlgorithms/Python`
   (add `--comments` if the body points to discussion). Summarize the
   requirements and the issue-linking convention (CLAUDE.md: "Part of #N" for
   tracking issues) before touching any code.
