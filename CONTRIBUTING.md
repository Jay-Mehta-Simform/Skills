# Contributing: the skill workflow

Every skill goes through the same six stages. The aim is that any skill in `skills/` can be traced back to a written brief and a passing set of evals, so quality is repeatable rather than accidental.

The current stage lives in the skill's `STATUS.md` frontmatter (`stage: ...`). `scripts/validate.py` checks that each skill has what its stage requires, so a stage cannot be skipped.

| # | Stage (`stage:`) | Where | You do | Required to advance |
|---|---|---|---|---|
| 1 | `propose` | `under-construction/` | `./scripts/new-skill.sh <name>`, fill in `BRIEF.md` | Brief complete (no `TODO`s); confirmed no existing skill covers this |
| 2 | `design` | `under-construction/` | Write `evals/evals.json` **before** the skill | ≥ 5 cases, ≥ 2 of them `should_trigger: false` |
| 3 | `draft` | `under-construction/` | Write `SKILL.md` (+ `scripts/`, `references/`, `assets/` as needed) | Valid frontmatter; description says *what* and *when*; ≤ 500 lines |
| 4 | `test` | `under-construction/` | Run the evals, fix, re-run; record `evals/results.md` | Every case passes; `Overall: PASS` recorded |
| 5 | `review` | PR | `./scripts/promote.sh <name>`, open a PR | Reviewer completes the PR checklist |
| 6 | `ready` | `skills/` | Merge | - |

Advance a stage by editing `stage:` in `STATUS.md` and adding a line to its log. Run `python3 scripts/validate.py` after every change.

**One-time setup:** the scripts need PyYAML. Install it into a project virtualenv (ignored by git), then activate it in each shell. `promote.sh` uses `.venv` automatically.

```
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
source .venv/bin/activate
```

---

## Stage 1: Propose

```
./scripts/new-skill.sh pdf-form-filler
```

This creates `under-construction/pdf-form-filler/` with `BRIEF.md`, `STATUS.md`, a starter `SKILL.md` and an empty `evals/evals.json`.

Fill in every section of `BRIEF.md`:

- **Problem**: what goes wrong or is slow today without this skill?
- **Users & context**: who asks for this, and in which product (Claude Code, claude.ai, API)?
- **Example requests**: at least 3 real phrasings that should trigger it.
- **Out of scope**: what it deliberately does *not* do, and nearby requests that should *not* trigger it.
- **Success criteria**: observable outcomes that will become eval assertions.
- **Overlap check**: which existing skills you checked, and why this one is still needed.

If the brief can't be written clearly, the skill isn't ready to build.

## Stage 2: Design (evals first)

Turn the brief into `evals/evals.json` **before** writing `SKILL.md`. This fixes the definition of "done" before you start.

```json
{
  "skill_name": "pdf-form-filler",
  "evals": [
    {
      "id": 1,
      "prompt": "Fill out this W-9 with my details: ...",
      "should_trigger": true,
      "expected_output": "A filled PDF with every required field populated",
      "assertions": ["Output file is a valid PDF", "Name field equals 'Jane Doe'"]
    },
    {
      "id": 2,
      "prompt": "Summarise this PDF for me",
      "should_trigger": false,
      "expected_output": "Skill does not load; a general summary is given"
    }
  ]
}
```

Rules:

- At least **5** cases: typical requests, edge cases (missing input, odd formats), and at least **2** near-miss requests that must **not** trigger the skill.
- `assertions` should be objectively checkable. Prefer "file X exists / field Y equals Z" over "output is good".
- Optional `files` key: paths (relative to `evals/`) to input files a case needs; keep them in `evals/files/`.

## Stage 3: Draft

Write `SKILL.md`.

**Frontmatter**

```yaml
---
name: pdf-form-filler          # must equal the folder name; lowercase, digits, hyphens; ≤ 64 chars
description: >-                # ≤ 1024 chars; third person; WHAT it does + WHEN to use it
  Fills in PDF forms from user-supplied data. Use when the user asks to
  fill, complete or populate a PDF form, or mentions W-9, I-9 or similar forms.
---
```

The `description` is the only part Claude sees before deciding to load the skill. Name the trigger words and contexts explicitly.

**Body guidelines**

- Keep `SKILL.md` under 500 lines. Move long reference material to `references/*.md` and link to it from `SKILL.md` ("read `references/field-types.md` when …"), so Claude loads it only when needed.
- Put deterministic or fiddly operations in `scripts/` and tell Claude to run them, rather than having it rewrite the logic each time.
- Put templates, fonts and sample files used in the output in `assets/`.
- Write instructions as steps, with one concrete example input and output.
- Say what to do when things go wrong (missing input, a script fails).
- Use relative links only; `validate.py` checks they resolve.

## Stage 4: Test

Run each case in `evals/evals.json` against the skill and record the run in `evals/results.md`. Any method works, as long as it is written down so the run can be repeated:

- **Recommended:** the `skill-creator` skill (in Claude Code: "use skill-creator to run the evals for under-construction/<name>"). It runs cases with and without the skill and grades assertions.
- **Manual:** install the skill locally (`ln -s "$PWD/under-construction/<name>" ~/.claude/skills/<name>`), run each prompt in a fresh session, and grade it.
- **Scripted (headless):** symlink the skill into a scratch project's `.claude/skills/`, then from that project run `claude -p "<prompt>" < /dev/null` once per case. The `< /dev/null` matters: without it, `claude -p` reads the rest of your loop's input as part of the prompt.

`evals/results.md` must contain:

- the date, method and model/product used
- a table with each case's id, PASS/FAIL and notes
- a final line, exactly `Overall: PASS` or `Overall: FAIL`

Iterate (fix `SKILL.md`, re-run, update results) until every case passes. If a case turns out to be wrong, fix the case and note the reason in `STATUS.md`. Do not delete a case just to get to green.

## Stage 5: Review & promote

1. Set `stage: review` in `STATUS.md`.
2. Run `./scripts/promote.sh <name>`. It runs the strict checks, moves the folder to `skills/`, sets `stage: ready`, and regenerates the README index and `marketplace.json`. Use `--dry-run` to only check.
3. Commit and open a PR. The PR template contains the promotion checklist. The reviewer reads `BRIEF.md`, `SKILL.md` and `evals/results.md` and ticks each item.

## Stage 6: Ready

Merge. The skill is now installable from the marketplace.

---

## Changing a ready skill

- **Small fixes** (wording, a bug in a script): edit in place in `skills/<name>/`, add a case to `evals/evals.json` covering the fix, re-run the evals, update `evals/results.md` and add a line to the `STATUS.md` log.
- **Large changes** (new scope, a rewrite): copy the skill to `under-construction/<name>-v2/`, revise `BRIEF.md`, and go through the stages again. On promotion, replace the old folder.

## Naming

- Kebab-case: `pdf-form-filler`, `release-notes`, `sql-reviewer`.
- Describe the job, not the technology alone (`csv-cleaner` rather than `pandas`).
- Must not contain `anthropic` or `claude`.

## What CI enforces

`python3 scripts/validate.py` (also run on every PR):

| Check | `under-construction/` | `skills/` |
|---|---|---|
| Folder name is valid kebab-case | ✓ | ✓ |
| `BRIEF.md` + `STATUS.md` with a valid `stage:` | ✓ | ✓ (`stage: ready`) |
| `evals.json` valid, ≥ 5 cases, ≥ 2 negatives | from `design` | ✓ |
| `SKILL.md` frontmatter valid, name = folder, ≤ 500 lines, relative links resolve | from `draft` | ✓ |
| `evals/results.md` exists | from `test` | ✓ with `Overall: PASS` |
| No `TODO` left in `BRIEF.md` / `SKILL.md` | from `review` | ✓ |
| README index + `marketplace.json` match `skills/` | - | ✓ |
