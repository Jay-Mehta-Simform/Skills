## Summary

<!-- What does this PR do? -->

## Type of change

- [ ] New skill promoted to `skills/`
- [ ] Change to an existing ready skill
- [ ] Work in progress in `under-construction/`
- [ ] Repo tooling / docs

## Promotion checklist (new or changed skills in `skills/` only)

**Brief**
- [ ] `BRIEF.md` states a real problem, at least 3 example requests, and explicit out-of-scope items
- [ ] The overlap check is convincing: no existing skill already covers this

**Evals**
- [ ] `evals/evals.json` covers typical requests, edge cases, and at least 2 near-miss requests that must not trigger
- [ ] Assertions are objectively checkable
- [ ] `evals/results.md` records the date, method and model, and every case passes
- [ ] No case was removed or weakened just to get to green (any change is explained in `STATUS.md`)

**Skill**
- [ ] The `description` says what the skill does and when to use it, with concrete trigger phrases
- [ ] `SKILL.md` is clear, step by step, includes an example, and says what to do on failure
- [ ] Long material is in `references/`; deterministic logic is in `scripts/`
- [ ] Scripts run without errors and have no hard-coded secrets or machine-specific paths

**Repo**
- [ ] `python3 scripts/validate.py` passes
