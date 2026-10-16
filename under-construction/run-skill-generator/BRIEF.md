# Brief: run-skill-generator

## Problem
Agents asked to run, screenshot or verify a project cold-start from the README every time, and READMEs describe the human path (`npm start`, a window opens) rather than a programmatic one. Each session re-fights the same install errors, launch crashes and feature gates. There is no persisted, verified recipe plus a driver that lets the next agent build, launch and interact with the app directly.

## Users & context
- Developers in Claude Code who want a project (or one app in a monorepo) to be drivable by future agents.
- The `verify` skill, which points here when it reports BLOCKED for lack of a way to launch the app.

## Example requests
Real phrasings that should trigger the skill:
1. "Create a run skill for this Express API so future agents can start and query it."
2. "Generate a run skill for the Electron app in apps/desktop."
3. "Verify got BLOCKED because nobody knows how to launch the CLI. Write the run skill for it."
4. "Update the run skill, the start command changed."

## Out of scope
- Running or screenshotting the app once without persisting a skill ("start the dev server and show me the homepage" must NOT trigger).
- Writing or editing the project README or human-facing docs ("write a README section on running locally" must NOT trigger).
- Verifying a specific change (belongs to `verify`).

## Success criteria
Observable outcomes; each becomes one or more eval assertions:
- Creates `<unit>/.claude/skills/run-<unit-name>/SKILL.md` whose frontmatter `name` equals the directory name and whose `description` includes run/start/build/test/screenshot verbs.
- The app was launched and interacted with in the session; for a GUI, a screenshot file exists on disk.
- An interaction harness is committed next to the skill (driver script, smoke script, or an inline `chromium-cli` heredoc for web apps).
- `SKILL.md` puts "Run (agent path)" before "Run (human path)".
- Every command in `SKILL.md` was actually run in the session.
- In a monorepo root, it asks which unit before writing anything.
- When a run skill already exists, it refines that skill and keeps its name instead of creating a second one.

## Overlap check
Checked this repo (`hello-world`, `verify`) and Claude Code built-ins (`run`, `init`). `run` launches an app for the current session but persists nothing; `init` writes a general `CLAUDE.md`, not a verified launch recipe with a driver; `verify` consumes run skills but does not write them beyond a short fallback note.
