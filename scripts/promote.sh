#!/usr/bin/env bash
# Promote a reviewed skill from under-construction/ to skills/.
# Usage: ./scripts/promote.sh [--dry-run] <skill-name>
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PY="$ROOT/.venv/bin/python3"
[[ -x "$PY" ]] || PY=python3
DRY_RUN=0
if [[ "${1:-}" == "--dry-run" ]]; then
  DRY_RUN=1
  shift
fi
NAME="${1:-}"
if [[ -z "$NAME" ]]; then
  echo "Usage: $0 [--dry-run] <skill-name>" >&2
  exit 1
fi

SRC="$ROOT/under-construction/$NAME"
DEST="$ROOT/skills/$NAME"
if [[ ! -d "$SRC" ]]; then
  echo "Error: under-construction/$NAME does not exist." >&2
  exit 1
fi
if [[ -e "$DEST" ]]; then
  echo "Error: skills/$NAME already exists. For a v2 rewrite, remove the old folder in the same PR." >&2
  exit 1
fi

"$PY" "$ROOT/scripts/validate.py" --promote "$NAME"

if (( DRY_RUN )); then
  echo "Dry run: under-construction/$NAME passes all promotion checks."
  exit 0
fi

if git -C "$ROOT" ls-files --error-unmatch "under-construction/$NAME" >/dev/null 2>&1; then
  git -C "$ROOT" mv "under-construction/$NAME" "skills/$NAME"
else
  mv "$SRC" "$DEST"
fi

"$PY" - "$DEST/STATUS.md" <<'PY'
import re, sys, datetime
path = sys.argv[1]
text = open(path, encoding="utf-8").read()
text = re.sub(r"^stage:.*$", "stage: ready  # propose | design | draft | test | review | ready",
              text, count=1, flags=re.M)
text = text.rstrip("\n") + f"\n- {datetime.date.today()}: Promoted to skills/ (stage: ready)\n"
open(path, "w", encoding="utf-8").write(text)
PY

"$PY" "$ROOT/scripts/sync_index.py"
"$PY" "$ROOT/scripts/validate.py"

echo
echo "Promoted $NAME to skills/. Next: commit, open a PR, and complete the checklist in the PR template."
