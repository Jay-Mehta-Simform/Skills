# Eval results: hello-world

- **Date:** 2026-10-16
- **Method:** Headless Claude Code CLI. The skill was symlinked into a scratch project's `.claude/skills/`, and each prompt ran in a fresh session: `claude -p "<prompt>" < /dev/null`. Outputs were graded by hand against the assertions in `evals.json`. Case 2 was run 5 times to check it is stable.
- **Product:** Claude Code CLI 2.1.301, default model

| Case | Should trigger | Triggered | Result | Notes |
|---|---|---|---|---|
| 1 | yes | yes | PASS | Exact confirmation text, 8 lines |
| 2 | yes | yes | PASS | Exact confirmation first in 5/5 runs; 2 runs added a one-line note that the skill loaded from a project copy, not the plugin |
| 3 | yes | yes | PASS | Exact confirmation text, 8 lines |
| 4 | no | no | PASS | Plain Rust hello-world program; the skill did not load |
| 5 | no | no | PASS | Ordinary greeting |
| 6 | no | no | PASS | General skill-loading troubleshooting; no confirmation text |

## History
- Run 1 (2026-10-08, case 1 only): **FAIL**. The model copied the code fence from SKILL.md, so the first line was ``````. Fixed by telling the skill to reply in plain text without the fence.
- Run 2 (2026-10-08): all cases **PASS**.
- Run 3 (2026-10-16, after renaming the source repo to `Jay-Mehta/Skills`): case 2 **FAIL** in 1 of 4 runs. The model inspected the plugin registry and led with an explanation instead of the confirmation. Fixed by stating in SKILL.md that loading from any location is the confirmation and that it must not inspect plugin registries or skill folders.
- Run 4 (2026-10-16): all cases **PASS** (table above).

Overall: PASS
