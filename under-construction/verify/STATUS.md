---
stage: draft  # propose | design | draft | test | review | ready
---

# Status: verify

## Open issues
- `BRIEF.md` and `evals/evals.json` were back-filled from the existing `SKILL.md` during the repo migration. Review them before moving to `test`.
- The evals need fixture projects (a small CLI with a `status --json` change, a server with a rate-limit change, a docs-only commit, a tests-only commit) in `evals/files/` before they can be run.

## Log
- 2026-10-16: Migrated into `under-construction/`. Added frontmatter, moved `examples/` to `references/`, back-filled `BRIEF.md` and 8 evals (3 negative) (stage: draft)
