# Brief: verify

## Problem
When asked whether a change works, agents tend to run the test suite, typecheck, or read the diff and declare success. None of that shows the change working in the running app. There is no repeatable protocol for finding the change, reaching the surface where it executes, probing around it, and reporting a verdict backed by captured evidence.

## Users & context
- Developers in Claude Code who have a change (uncommitted work, a branch, a commit or a PR) and want runtime confirmation before review or merge.
- Agents that just implemented a change and need to confirm it at the real interface.

## Example requests
Real phrasings that should trigger the skill:
1. "Verify my change works."
2. "Can you check this PR actually adds the Retry-After header to 429 responses?"
3. "Run the CLI and confirm the new `--json` flag on `status` works."
4. "Smoke-test this branch before I open a PR."

## Out of scope
- Running the test suite or typechecking ("run the tests", "does it typecheck?" must NOT trigger).
- Code review by reading ("review this diff for bugs" must NOT trigger).
- Writing tests.
- Creating a run skill for a project ("create a run skill" belongs to `run-skill-generator`); verify only hands off to it when BLOCKED.

## Success criteria
Observable outcomes; each becomes one or more eval assertions:
- The final message is a report with a `## Verification:` heading and a `**Verdict:**` of exactly one of PASS, FAIL, BLOCKED or SKIP.
- Steps are actions on the running app with captured output (stdout, response bodies, screenshots), not test or typecheck runs.
- At least one step is a 🔍 probe off the happy path.
- Before a cold start, it checks `.claude/skills/` (repo root and touched dirs) for `verifier-*` and `run-*` skills.
- A docs-only or tests-only change gets SKIP with a one-line reason and no build or test run.
- When the app cannot be reached, the verdict is BLOCKED with where it stopped and a `/run-skill-generator` prompt.
- Outside a git repo with no stated scope, it asks what to verify instead of guessing.

## Overlap check
Checked this repo (`hello-world`, `run-skill-generator`) and Claude Code built-ins (`run`, `code-review`, `simplify`). `run` launches an app but gives no verdict on a specific change; `code-review` and `simplify` read code without running it; `run-skill-generator` produces a reusable launch recipe rather than a verdict. None produce an evidence-backed runtime verdict for a diff.
