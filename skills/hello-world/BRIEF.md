# Brief: hello-world

## Problem
After installing this repo's marketplace plugin, or copying a skill into `~/.claude/skills/`, there is no quick way to confirm that skills from this repo actually load. It also helps new contributors to have one small, complete skill that shows every convention in this repo.

## Users & context
- Anyone who has just installed the `skills` plugin from this marketplace in Claude Code, or uploaded a skill to claude.ai.
- Contributors reading the repo who want a minimal, complete example of a promoted skill.

## Example requests
1. "Run the hello-world skill."
2. "Check that the Jay-Mehta skills plugin is installed and working."
3. "Hello world skill - are my skills from the skills repo loading?"

## Out of scope
- Writing "Hello, World!" programs in any programming language ("write hello world in Rust" must NOT trigger).
- General greetings ("hello", "hi Claude") must NOT trigger.
- Diagnosing why other, unrelated skills or plugins fail to load.

## Success criteria
- When triggered, the reply starts with the exact line `hello-world skill loaded ✓`.
- The reply names the source repository `Jay-Mehta/Skills`.
- The reply lists the files every skill in this repo has (SKILL.md, BRIEF.md, STATUS.md, evals/evals.json, evals/results.md).
- The reply is short (under 15 lines) and asks no follow-up questions.
- The skill is not used for programming hello-world requests or plain greetings.

## Overlap check
Checked this repo (no other skills yet) and the built-in skills available in Claude Code and claude.ai. None of them confirm that this specific repo is installed. A skill is the right shape because loading it is itself the check.
