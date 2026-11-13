---
description: Verify, push, and open a PR in the FORK only.
---

1. Use the `check-runner` subagent. Stop if anything fails.
2. Use the `contributing-reviewer` subagent. Stop if the verdict is FAIL.
3. `git push -u origin HEAD`
4. Write the PR body to a temp file (outside the repo) from
   `.github/pull_request_template.md`. Fill it in honestly:
   - tick only the boxes that are true, and at least one under
     "Describe your change" (the algorithms-keeper bot closes PRs without one);
   - say the change is AI-assisted (Claude Code), per CS440 policy;
   - write "Part of #15187", never "Fixes #15187";
   - include the ty output before and after, and explain why `None` replaces
     the `-1` sentinel;
   - end with the Claude Code attribution line.
5. Open the PR on the fork:

   ```bash
   gh pr create --repo Andyhim/Python --base master --head "$(git branch --show-current)" \
     --title "<conventional commit title>" --body-file <temp body file>
   ```

6. Print the PR URL and confirm it starts with `https://github.com/Andyhim/Python/pull/`.
