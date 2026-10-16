---
name: hello-world
description: Confirms that skills from the Jay-Mehta/Skills repository are installed and loading correctly, and shows the conventions every skill in this repo follows. Use when the user asks to test, verify or check that the skills repo or its plugin is installed, or says "hello world skill" or "run the hello-world skill".
---

# hello-world

An installation check for the `Jay-Mehta/Skills` repository. The skill being loaded at all shows that installation worked, so the response only needs to confirm that and briefly show the repo's conventions.

## When to use

- The user asks to run or test the hello-world skill.
- The user asks whether skills or the plugin from `Jay-Mehta/Skills` are installed or loading.

Do **not** use for writing "Hello, World!" programs, for ordinary greetings, or for troubleshooting other skills.

## Steps

1. Reply with the confirmation below as plain text: the lines inside the block, exactly as written, without the surrounding code fence and with no other content.
2. Do not inspect plugin registries, settings or skill folders. Loading this skill from any location (the plugin, `~/.claude/skills/` or a project's `.claude/skills/`) is the confirmation.
3. Do not ask follow-up questions or offer further help.

## Response

```
hello-world skill loaded ✓
Source: Jay-Mehta/Skills
Every skill in this repo contains:
- SKILL.md: instructions + frontmatter (name, description)
- BRIEF.md: problem, scope and success criteria
- STATUS.md: lifecycle stage and log
- evals/evals.json: test prompts, including ones that must not trigger
- evals/results.md: the latest eval run
```

## If something goes wrong

There is nothing to fail: if this skill is running, it loaded. If the user expected other skills from this repo and they are missing, suggest re-running `/plugin install skills@jay-mehta-skills` in Claude Code.
