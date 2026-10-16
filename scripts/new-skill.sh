#!/usr/bin/env bash
# Start a new skill in under-construction/ at stage "propose".
# Usage: ./scripts/new-skill.sh <skill-name>
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
NAME="${1:-}"

if [[ -z "$NAME" ]]; then
  echo "Usage: $0 <skill-name>" >&2
  exit 1
fi
if [[ ! "$NAME" =~ ^[a-z0-9]+(-[a-z0-9]+)*$ ]] || (( ${#NAME} > 64 )); then
  echo "Error: name must be kebab-case (a-z, 0-9, hyphens), at most 64 chars." >&2
  exit 1
fi
if [[ "$NAME" == *anthropic* || "$NAME" == *claude* ]]; then
  echo "Error: name must not contain 'anthropic' or 'claude'." >&2
  exit 1
fi
for dir in under-construction skills; do
  if [[ -e "$ROOT/$dir/$NAME" ]]; then
    echo "Error: $dir/$NAME already exists." >&2
    exit 1
  fi
done

DIR="$ROOT/under-construction/$NAME"
TODAY="$(date +%Y-%m-%d)"
mkdir -p "$DIR/evals"

cat > "$DIR/BRIEF.md" <<EOF
# Brief: $NAME

## Problem
TODO: What goes wrong or is slow today without this skill?

## Users & context
TODO: Who asks for this, and in which product (Claude Code, claude.ai, API)?

## Example requests
Real phrasings that should trigger the skill (at least 3):
1. TODO
2. TODO
3. TODO

## Out of scope
TODO: What the skill deliberately does not do, and nearby requests that should NOT trigger it.

## Success criteria
Observable outcomes; each becomes one or more eval assertions:
- TODO

## Overlap check
TODO: Existing skills checked (in this repo and built-in), and why this one is still needed.
EOF

cat > "$DIR/STATUS.md" <<EOF
---
stage: propose  # propose | design | draft | test | review | ready
---

# Status: $NAME

## Open issues
- None yet

## Log
- $TODAY: Created (stage: propose)
EOF

cat > "$DIR/SKILL.md" <<EOF
---
name: $NAME
description: TODO What this skill does, in the third person. Use when TODO (trigger phrases and contexts).
---

# $NAME

TODO: One-paragraph overview of what this skill does.

## When to use
TODO

## Steps
1. TODO

## Example
**Input:** TODO

**Output:** TODO

## If something goes wrong
TODO
EOF

cat > "$DIR/evals/evals.json" <<EOF
{
  "skill_name": "$NAME",
  "evals": []
}
EOF

echo "Created under-construction/$NAME (stage: propose)."
echo "Next: fill in under-construction/$NAME/BRIEF.md, then set stage: design in STATUS.md."
