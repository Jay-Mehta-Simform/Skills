#!/usr/bin/env python3
"""Validate every skill in skills/ and under-construction/.

Skills in under-construction/ are checked according to their STATUS.md stage;
skills in skills/ get the full, strict set of checks. See CONTRIBUTING.md.

Usage:
    python3 scripts/validate.py                 # validate the whole repo
    python3 scripts/validate.py --promote NAME  # strict checks for under-construction/NAME
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sync_index import out_of_date, read_frontmatter  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
STAGES = ["propose", "design", "draft", "test", "review", "ready"]
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)")
MAX_NAME = 64
MAX_DESCRIPTION = 1024
MAX_SKILL_LINES = 500
MIN_EVALS = 5
MIN_NEGATIVE_EVALS = 2


def at_least(stage, minimum):
    return STAGES.index(stage) >= STAGES.index(minimum)


def check_name(name, errors):
    if not NAME_RE.match(name) or len(name) > MAX_NAME:
        errors.append(f"folder name '{name}' must be kebab-case (a-z, 0-9, hyphens), ≤ {MAX_NAME} chars")
    if "anthropic" in name or "claude" in name:
        errors.append(f"folder name '{name}' must not contain 'anthropic' or 'claude'")


def check_status(skill_dir, errors):
    """Return the stage from STATUS.md frontmatter, or None if missing/invalid."""
    path = skill_dir / "STATUS.md"
    if not path.exists():
        errors.append("missing STATUS.md")
        return None
    stage = (read_frontmatter(path) or {}).get("stage")
    if stage not in STAGES:
        errors.append(f"STATUS.md frontmatter 'stage' must be one of {', '.join(STAGES)} (got {stage!r})")
        return None
    return stage


def check_evals(skill_dir, errors):
    path = skill_dir / "evals" / "evals.json"
    if not path.exists():
        errors.append("missing evals/evals.json")
        return
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        errors.append(f"evals/evals.json is not valid JSON: {e}")
        return
    if data.get("skill_name") != skill_dir.name:
        errors.append(f"evals/evals.json 'skill_name' must be '{skill_dir.name}'")
    cases = data.get("evals")
    if not isinstance(cases, list):
        errors.append("evals/evals.json must have an 'evals' list")
        return
    if len(cases) < MIN_EVALS:
        errors.append(f"evals/evals.json needs ≥ {MIN_EVALS} cases (has {len(cases)})")
    ids = set()
    negatives = 0
    for i, case in enumerate(cases):
        where = f"evals/evals.json case #{i + 1}"
        if not isinstance(case, dict):
            errors.append(f"{where} must be an object")
            continue
        if case.get("id") in ids:
            errors.append(f"{where} has duplicate id {case.get('id')!r}")
        ids.add(case.get("id"))
        if not isinstance(case.get("prompt"), str) or not case["prompt"].strip():
            errors.append(f"{where} needs a non-empty 'prompt'")
        if not isinstance(case.get("should_trigger"), bool):
            errors.append(f"{where} needs 'should_trigger': true/false")
        elif not case["should_trigger"]:
            negatives += 1
        for f in case.get("files", []):
            if not (skill_dir / "evals" / f).exists():
                errors.append(f"{where} references missing file evals/{f}")
    if negatives < MIN_NEGATIVE_EVALS:
        errors.append(f"evals/evals.json needs ≥ {MIN_NEGATIVE_EVALS} cases with should_trigger: false (has {negatives})")


def check_skill_md(skill_dir, errors):
    path = skill_dir / "SKILL.md"
    if not path.exists():
        errors.append("missing SKILL.md")
        return
    fm = read_frontmatter(path)
    if fm is None:
        errors.append("SKILL.md must start with valid YAML frontmatter between '---' lines")
        return
    if fm.get("name") != skill_dir.name:
        errors.append(f"SKILL.md 'name' must equal the folder name '{skill_dir.name}' (got {fm.get('name')!r})")
    description = fm.get("description")
    if not isinstance(description, str) or not description.strip():
        errors.append("SKILL.md needs a non-empty 'description'")
    else:
        if len(description) > MAX_DESCRIPTION:
            errors.append(f"SKILL.md 'description' is {len(description)} chars (max {MAX_DESCRIPTION})")
        if re.search(r"<[^>]+>", description):
            errors.append("SKILL.md 'description' must not contain XML/HTML tags")
    lines = path.read_text(encoding="utf-8").count("\n") + 1
    if lines > MAX_SKILL_LINES:
        errors.append(f"SKILL.md is {lines} lines (max {MAX_SKILL_LINES}); move detail into references/")


def check_links(skill_dir, errors):
    for md in skill_dir.rglob("*.md"):
        for target in LINK_RE.findall(md.read_text(encoding="utf-8")):
            if re.match(r"^(https?:|mailto:|#)", target):
                continue
            if not (md.parent / target.split("#")[0]).exists():
                errors.append(f"{md.relative_to(skill_dir)} links to missing file '{target}'")


def check_results(skill_dir, errors, require_pass):
    path = skill_dir / "evals" / "results.md"
    if not path.exists():
        errors.append("missing evals/results.md")
        return
    if require_pass and not re.search(r"^Overall:\s*PASS\s*$", path.read_text(encoding="utf-8"), re.M):
        errors.append("evals/results.md must contain the line 'Overall: PASS'")


def check_no_todos(skill_dir, errors):
    for name in ("BRIEF.md", "SKILL.md"):
        path = skill_dir / name
        if path.exists() and "TODO" in path.read_text(encoding="utf-8"):
            errors.append(f"{name} still contains TODO placeholders")


def validate_skill(skill_dir, strict):
    """Return a list of error strings for one skill folder.

    strict=True applies every check regardless of stage (used for skills/ and promotion).
    """
    errors = []
    check_name(skill_dir.name, errors)
    if not (skill_dir / "BRIEF.md").exists():
        errors.append("missing BRIEF.md")
    stage = check_status(skill_dir, errors)
    if stage is None and not strict:
        return errors
    effective = "ready" if strict else stage

    if at_least(effective, "design"):
        check_evals(skill_dir, errors)
    if at_least(effective, "draft"):
        check_skill_md(skill_dir, errors)
        check_links(skill_dir, errors)
    if at_least(effective, "test"):
        check_results(skill_dir, errors, require_pass=at_least(effective, "review"))
    if at_least(effective, "review"):
        check_no_todos(skill_dir, errors)
    return errors


def read_stage(skill_dir):
    path = skill_dir / "STATUS.md"
    return (read_frontmatter(path) or {}).get("stage") if path.exists() else None


def skill_dirs(parent):
    return sorted(p for p in (ROOT / parent).iterdir() if p.is_dir()) if (ROOT / parent).exists() else []


def report(label, errors):
    if errors:
        print(f"✗ {label}")
        for e in errors:
            print(f"    - {e}")
    else:
        print(f"✓ {label}")


def validate_repo():
    failed = False
    for skill_dir in skill_dirs("skills"):
        errors = validate_skill(skill_dir, strict=True)
        stage = read_stage(skill_dir)
        if stage is not None and stage != "ready":
            errors.append(f"skills in skills/ must have stage: ready (got {stage!r})")
        report(f"skills/{skill_dir.name}", errors)
        failed |= bool(errors)

    for skill_dir in skill_dirs("under-construction"):
        errors = validate_skill(skill_dir, strict=False)
        stage = read_stage(skill_dir)
        if stage == "ready":
            errors.append("stage: ready is only valid in skills/; run scripts/promote.sh")
        if (ROOT / "skills" / skill_dir.name).exists():
            errors.append(f"a ready skill named '{skill_dir.name}' already exists in skills/")
        report(f"under-construction/{skill_dir.name} [{stage or '?'}]", errors)
        failed |= bool(errors)

    stale = out_of_date()
    report("README index + marketplace.json in sync", [f"{p} is out of date; run: python3 scripts/sync_index.py" for p in stale])
    failed |= bool(stale)
    return failed


def main():
    args = sys.argv[1:]
    if args[:1] == ["--promote"] and len(args) == 2:
        skill_dir = ROOT / "under-construction" / args[1]
        if not skill_dir.is_dir():
            sys.exit(f"under-construction/{args[1]} does not exist")
        errors = validate_skill(skill_dir, strict=True)
        stage = read_stage(skill_dir)
        if stage != "review":
            errors.append(f"STATUS.md stage must be 'review' to promote (got {stage!r})")
        report(f"under-construction/{args[1]} ready for promotion", errors)
        sys.exit(1 if errors else 0)
    if args:
        sys.exit(__doc__)
    sys.exit(1 if validate_repo() else 0)


if __name__ == "__main__":
    main()
