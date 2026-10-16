---
stage: draft  # propose | design | draft | test | review | ready
---

# Status: run-skill-generator

## Open issues
- `BRIEF.md` and `evals/evals.json` were back-filled from the existing `SKILL.md` during the repo migration. Review them before moving to `test`.
- The evals need fixture projects (an Express API, an Electron app inside a monorepo, a small CLI, a project with an existing `run-api` skill) in `evals/files/` before they can be run.

## Log
- 2026-10-16: Migrated into `under-construction/`. Added frontmatter, moved `examples/` to `references/` and `template.md` to `assets/`, back-filled `BRIEF.md` and 8 evals (3 negative) (stage: draft)
