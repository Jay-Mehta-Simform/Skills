# Landscape of existing review and verification tools

Research for GitHub issue #2. Surveyed 2026-10-26.

**Question.** What do existing review and verification skills and tools already cover, and where are their gaps against our candidate concerns (spec gaps, spec alignment, maintainability, emergent edge cases, trust-boundary bypass, user-perspective behaviour)?

**Vocabulary.** Terms follow `GLOSSARY.md` `## Assurance` [S46]: **review** judges an artifact by reading it against a reference; **verification** produces evidence by executing something; a **checkpoint** is where an artifact (a spec, a change) is assured; a **concern** is one thing assurance looks for.

**Method.** Every claim cites a source in the [Sources](#sources) list as `[Sn]`. Primary sources only: official product docs, first-party changelogs and engineering blogs, and the skill or prompt files themselves (local plugin cache copies, GitHub raw files pinned where possible, and for Claude Code's bundled skills, prompt text extracted from the installed v2.1.310 binary). Where a source is silent, this document says "not documented" instead of guessing. Lines marked **Analysis** are this document's inference, not a source's claim.

---

## Key findings

1. **Every PR-time reviewer starts from the diff.** Context beyond it is bolted on in different amounts: callers of changed functions (Claude Code `/code-review` cross-file angle [S11]), whole-repo agentic exploration (Copilot [S32][S36], CodeRabbit [S27], Bugbot [S23]), git history and past PRs (the marketplace `code-review` plugin [S19]), a code graph and linked repos (CodeRabbit [S30]). None takes the *product or system* as its unit; the "overall picture" exists only as an altitude angle (Claude Code [S11]), sequence diagrams and architecture suggestions (CodeRabbit [S25][S29]), or Matt Pocock's advice to run one final pass over a whole branch to catch cross-ticket interactions [S2].
2. **Intent is optional input almost everywhere, and missing intent is mostly silent.** Claude Code's bundled `/code-review`, the managed Code Review service, Bugbot and Copilot document no spec or ticket input at all [S10][S13][S22][S33]. Only four tools say what they do without it: Matt Pocock's `code-review` asks, then skips its Spec axis and reports "no spec available" [S1]; BMAD asks for a plan, runs in "no-plan mode", announces the skipped intent lens and hands judgement calls back to the user [S41][S42]; CodeRabbit returns `Unclear` / `Inconclusive` verdicts [S24][S28]; Spec Kit `analyze` aborts [S37].
3. **Spec alignment is covered by three tools, all by reading.** Matt Pocock's Spec axis (missing, scope creep, wrong implementation, each quoting the spec line) [S1], CodeRabbit's linked-issue assessment over issue title and description only [S24], and BMAD's Intent Alignment Auditor, which enumerates the defensible readings of the intent and names which one the diff implements [S41].
4. **Spec gaps (a spec reviewed *before* code) are a separate tool category** that PR reviewers never touch: Spec Kit `clarify` / `analyze` / `checklist` [S37][S38][S39], Kiro's Analyze Requirements [S40], BMAD's PRD rubric, architecture reviewer gate and ticket validation checks [S43][S44][S45], and CodeRabbit Issue Planner (human review of an AI plan) [S31]. Spec Kit `checklist` explicitly refuses to verify behaviour: it tests the requirements, not the product [S38].
5. **Execution is rare.** Among reviewers, only ultrareview says every finding is "independently reproduced and verified" [S12]. CodeRabbit and Copilot execute static analysers (50+ linters/SAST; CodeQL, ESLint, PMD) [S26][S35], which is execution of a tool, not of the change. Bugbot lists running code to verify its own reports as future work [S23]. Claude Code's bundled `/verify` and our in-house `verify` are the only tools that drive the running app at the user's surface [S16][S8].
6. **Nobody verifies a trust-boundary bypass by attempting it.** `/security-review` and the `claude-security` plugin hunt auth bypass and privilege escalation by reading and tracing, with refutation voting, and are explicitly read-only [S18][S21]. `/security-review` also excludes several classes by rule (DoS, rate limiting, client-side authz checks treated as non-issues) [S18]. The glossary's definition of verification includes "attempting to exploit it" [S46]; no surveyed tool does that.
7. **Two designs from BMAD address the user's thesis directly.** Its reviewer lenses are context-free subagents, and the author's narrative (commit messages, description) is staged in a separate claims file that only the Edge Case Hunter reads, and only *after* it has finished tracing paths, "so the claims cannot steer it retroactively" [S41]. Its Verification Gap lens asks which changed behaviours could regress without any test failing [S41]. Both are reading techniques, not execution.
8. **Where the review rules come from differs, and matters when the author is an AI.** Claude's managed Code Review reads `REVIEW.md` from the base branch "never from the pull request's own changes" [S13][S14], and Bugbot reads its config from the base branch so "a PR cannot change how Bugbot reviews itself" [S22]. Copilot reads instructions and skills from the head branch [S33].

---

## Per-tool profiles

Each profile answers the same six questions: **Reads** (artifact), **Reference** (what it judges against), **Executes** (anything run), **Context beyond the diff**, **Output**, **When context is missing**.

### A. Matt Pocock skills (mattpocock-skills 1.3.1)

#### `code-review`

| Field | Finding |
| --- | --- |
| Reads | `git diff <fixed-point>...HEAD` plus `git log` commit list; the user must name the fixed point, and it fails early on a bad ref or empty diff [S1]. Three-dot form excludes uncommitted work, so commit first [S2]. |
| Reference | Two separate axes. **Standards**: every repo file documenting how code is written (`CODING_STANDARDS.md`, `CONTRIBUTING.md` mandatory if present) plus a baseline of 12 Fowler smells; the repo always overrides the baseline, and smells are always judgement calls [S1]. **Spec**: the originating issue/spec, found via issue refs in commits, a passed path, a file under `docs/`, `specs/`, `.scratch/`, or by asking [S1]. |
| Executes | Nothing. Two parallel read-only sub-agents [S1]. |
| Context beyond the diff | Only the standards files and the spec. Does not read `GLOSSARY.md` or ADRs (those are read by `tdd` and `to-spec`, not by `code-review`) [S1][S5][S6]. |
| Output | `## Standards` and `## Spec` reports, each under 400 words, never merged or reranked, ending with the worst issue per axis [S1]. Standards findings cite the rule or name the smell; Spec findings quote the spec line [S1][S2]. |
| Missing context | No fixed point: asks. No spec: asks; if the user says there is none, the Spec sub-agent is skipped and the report says "no spec available" rather than inferring requirements [S1][S2]. No standards: falls back to the smell baseline [S2]. |

Notes from its own docs [S2]: it does not hunt bugs ("null paths, races, off-by-one" are deferred to Claude Code's built-in review); findings are "a hypothesis, not evidence" and are not re-verified; there is "no convergence guarantee" across reruns; and reviewing in the authoring session is "confirmation bias with a slash command", so a fresh session is preferred.

**How review is invoked in the chain.** `implement` runs `tdd` at pre-agreed seams, then calls `code-review` itself before committing [S3]. `implement-spec` runs `tdd` per ticket in parallel worktrees and calls `code-review` once on the integration branch at the end, fixing all findings in one implementer subagent [S4]. `tdd` places refactoring in "the review stage (see the `code-review` skill)", not the red-green loop [S5]. `to-spec` writes a spec with user stories, implementation and testing decisions, and confirms test seams with the user, but does not review the spec [S6]. The documented chain is `grill-with-docs -> to-spec -> to-tickets -> implement -> code-review -> retro` [S2]; `grill-with-docs` is an interview that combines `grilling` and `domain-modeling` [S7].

**Analysis.** Review happens at one checkpoint (the finished change), inside the authoring session when invoked by `implement` [S3], which its own docs flag as a weakness [S2]. There is no checkpoint that reviews the spec as an artifact; `grill-with-docs` sharpens a plan by interview, before the spec exists.

### B. In-house building block

#### `under-construction/verify` (this repo, stage `draft`)

| Field | Finding |
| --- | --- |
| Reads | The full change range (`@{u}..`, `origin/HEAD...`, `HEAD`, or `gh pr diff`), plus any description. "The diff is ground truth. Any description is a claim about it." A mismatch is a finding [S8]. |
| Reference | The claim (description and/or the agent's read of the diff) [S8]. |
| Executes | Yes, that is the whole point: build, run, drive the app to where the changed code executes at its **surface** (terminal, socket, pixels, package boundary, agent, CI), then probe around it. Explicitly forbids running tests, typechecking, or import-and-call [S8]. |
| Context beyond the diff | `.claude/skills/` at the repo root and touched package dirs for `verifier-*` / `run-*` skills; otherwise README / `package.json` / Makefile cold start, then persists the recipe as `.claude/skills/verify/SKILL.md` [S8]. |
| Output | `## Verification:` report, verdict PASS / FAIL / BLOCKED / SKIP, numbered steps with captured evidence, at least one 🔍 probe off the happy path, and a Findings section with a deliberately low bar ("would I mention this if they were sitting next to me") [S8]. |
| Missing context | No repo and no stated scope: asks. App unreachable: BLOCKED with where it stopped plus a `/run-skill-generator` prompt. No runtime surface: SKIP with one line. "When in doubt, FAIL." [S8] |

Its probe catalogue (empty or conflicting flags, malformed bodies, Ctrl-C mid-operation, doing it twice or in two sessions) is the only surveyed mechanism that hunts **emergent edge cases by execution** [S8]. It skips destructive paths with no safe target and says so [S8]. Its behaviour matches the documented Claude Code bundled `/verify` (same recipe file location and replacement rule) [S16]. The `BRIEF.md` overlap check treats `run`, `code-review` and `simplify` as the nearest built-ins and concludes none gives "an evidence-backed runtime verdict for a diff" [S8].

### C. Claude Code (v2.1.310) and Anthropic plugins

#### `/code-review` (bundled skill; alias `/review`)

| Field | Finding |
| --- | --- |
| Reads | Current branch ahead of upstream plus uncommitted changes, or a PR number, branch, path, or revision range [S10]. |
| Reference | Correctness by default; cleanup (reuse, simplification, efficiency), altitude and CLAUDE.md conventions depending on model and effort [S10][S11]. Follows `CLAUDE.md`; does not read `REVIEW.md` [S10]. No spec, issue or PR-description input is documented [S10]. |
| Executes | No build or run. At `medium` and above, finder angles run as subagents and each candidate goes to one verifier subagent that votes CONFIRMED / PLAUSIBLE / REFUTED by reading the code [S11]. |
| Context beyond the diff | Varies sharply by effort [S11]. `low`: no subagents and no full-file reads, test hunks skipped, nothing flagged outside the hunk. `medium`/`high`: 3 correctness angles (line-by-line scan reading the enclosing function, removed-behaviour auditor, cross-file tracer that greps callers and callees) + 3 cleanup + 1 altitude + 1 conventions. `xhigh`/`max`: adds language-pitfall and wrapper/proxy angles plus a gap-sweep pass. The conventions angle reads user, repo-root and ancestor `CLAUDE.md` files and only flags a violation it can quote [S11]. |
| Output | Text in the conversation, or a `ReportFindings` tool call with `file`, `line`, `summary`, `failure_scenario`, `category` (`correctness`, `simplification`, `efficiency`, `reuse`, `altitude`, `conventions`, or a narrower slug), ranked most severe first, capped (32 via the tool, configurable with `--max-findings`) [S10][S11]. `--fix` applies findings; `--comment` posts inline PR comments [S10]. |
| Missing context | If the subagent tool is unavailable it runs every angle inline and must disclose that it was a single-pass review, so the reader knows what actually ran [S11]. No CLAUDE.md: the conventions angle returns nothing [S11]. No behaviour for missing intent is documented. |

The bundled prompt tells Claude, after reporting, to invoke `/verify` if it has not run this session and the diff has a runtime surface, framing review as checking that the diff reads right and `/verify` as checking that it runs right [S11]. The altitude angle asks whether each change fixes the root cause at the right depth instead of patching a symptom [S11], the closest any bundled reviewer comes to a whole-system concern.

#### `/code-review ultra` (ultrareview)

Runs a larger fleet of reviewer agents in a cloud sandbox over the branch versus the default branch (or a PR), for about 15 to 25 minutes [S12]. "Every reported finding is independently reproduced and verified, so the results focus on real bugs rather than style suggestions" [S12]. The docs do not say how reproduction is done. Free text after the command becomes a note the findings are related to, the only intent channel documented for any Claude Code reviewer [S12][S10]. Refuses diffs above 500 files or 8,000 lines by default [S12].

#### Managed Code Review (GitHub service, Team and Enterprise)

| Field | Finding |
| --- | --- |
| Reads | "The diff and the surrounding code" [S13]. |
| Reference | Default focus "on correctness: bugs that would break production, not formatting preferences or missing test coverage" [S13]; repo `CLAUDE.md` files (root and ancestors of changed files) and `REVIEW.md` [S14]. |
| Executes | No: "without building or running your code" [S13]. |
| Context beyond the diff | Surrounding code; on later reviews, replies on its earlier findings [S15]. `REVIEW.md` is read from the base or default branch, never the PR [S13][S14]. |
| Output | Inline comments marked 🔴 Important, 🟡 Nit, 🟣 Pre-existing, a summary, a neutral check run (never a failure), and a machine-readable severity line for CI gating [S15]. |
| Missing context | Not documented beyond `REVIEW.md` fallback rules for unprotected branches [S14]. |

Pipeline: find (parallel agents), verify (filter false positives against the code), rank, post [S13].

#### `/simplify` (bundled)

Four parallel cleanup agents (reuse, simplification, efficiency, altitude) that apply fixes and explicitly do not hunt for correctness bugs [S11][S9]. A maintainability tool that writes code, not a reviewer that reports.

#### `/security-review` (built-in command and GitHub Action)

| Field | Finding |
| --- | --- |
| Reads | `git diff --merge-base origin/HEAD`, changed file list, log, status [S18]. |
| Reference | Existing security patterns and threat model of the repo, then OWASP-style categories: injection, authn/authz (auth bypass, privilege escalation, session, JWT), crypto and secrets, code execution, data exposure [S17][S18]. |
| Executes | No. Allowed tools are read-only git commands plus Read/Glob/Grep; the prompt does not run or reproduce exploits [S18]. |
| Context beyond the diff | Phase 1 "Repository Context Research" (existing frameworks, sanitisation patterns, threat model), Phase 2 compares the change against them, Phase 3 traces data flow from inputs to sensitive operations [S18]. |
| Output | Markdown, one section per vulnerability with severity, description, exploit scenario and fix [S18]; the Action posts line comments and a JSON results file [S17]. |
| Missing context | Not documented. Hard exclusions remove 17 classes (DoS, rate limiting, missing hardening, theoretical races, test-only files, missing audit logs, and others); precedents treat client-side authorisation checks as non-vulnerabilities and env vars / CLI flags as trusted; only findings above 80% confidence of exploitability are kept [S18]. "Not hardened against prompt injection" [S17]. |

#### `/verify` and `/run` (bundled)

`/verify` builds and runs the app "to confirm a code change does what it should, without falling back to tests or type checks"; `/run` launches and drives the app; `/run-skill-generator` records a per-project launch recipe [S16][S9]. `/verify` runs only when invoked [S9]. See the in-house `verify` profile for the protocol.

#### Anthropic marketplace plugins (local copies)

- **`code-review` plugin** (the original public `/code-review` command): checks eligibility, gathers CLAUDE.md paths, summarises the PR, then 5 parallel agents: CLAUDE.md compliance, a "shallow scan for obvious bugs" that should "avoid reading extra context beyond the changes", git blame/history, comments on previous PRs touching the same files, and in-code comment guidance; each issue is scored 0 to 100 and only 80 or above is posted [S19]. It lists "general code quality issues" and "issues that a linter, typechecker, or compiler would catch" as false positives, and says not to build or typecheck [S19].
- **`pr-review-toolkit`**: specialised agents for comments, tests (`pr-test-analyzer`), silent failures, type design, general code and simplification, aggregated into Critical / Important / Suggestions / Strengths [S20]. Driven by `git diff --name-only` [S20].
- **`claude-security`**: threat-model-first security scan of a diff or the whole repo; each candidate faces three read-only verifier voters (reachability, impact, defenses) who "Default to FALSE_POSITIVE" unless they can cite the attacker-controlled source, the sink and the absence of mitigation; it must name "who authors the input" and whether the code may trust them [S21]. Patches are developed in a scratch copy and reviewed by independent agents [S21]. No exploit is executed [S21].

### D. Third-party PR reviewers

#### Cursor Bugbot

| Field | Finding |
| --- | --- |
| Reads | PR diffs, incremental since its last review by default; skips credential-like files and generated files [S22]. |
| Reference | `.cursor/BUGBOT.md` (root always, nested for matching files) plus team, repo, learned and manual rules [S22]. Rules exist to "encode codebase-specific invariants like unsafe migrations or incorrect use of internal APIs" [S23]. Linked issues and PR descriptions are not documented as inputs [S22]. |
| Executes | No. Running code to verify its own reports is described as future work [S23]. |
| Context beyond the diff | Agentic: "reason over the diff, call tools, and decide where to dig deeper" and "pulled in the additional context it needed at runtime" [S23]; reads prior PR comments; MCP tools on Team/Enterprise [S22]. Config from the base branch only [S22]. |
| Output | PR comments with explanation and fix suggestion, severity in the API, CI status (`neutral` by default), Fix in Cursor / Web links, optional Autofix cloud agent [S22]. Quality is tracked as a "resolution rate": an AI judge checks at merge time which flagged bugs the author actually fixed [S23]. |
| Missing context | Missing config: previous behaviour; invalid fields ignored; rules truncated at 30,000 characters each and 100,000 combined, visible via verbose mode; oversized PRs skipped with a request to split [S22]. Unclear intent: not documented [S22]. |

#### CodeRabbit

| Field | Finding |
| --- | --- |
| Reads | The PR, with the full repository cloned into a sandbox [S27]. |
| Reference | Coding guideline files it auto-detects (`.cursorrules`, `CLAUDE.md`, `AGENTS.md`), path and ast-grep instructions, learnings, and linked issues (title, description, Jira custom fields; not comments) [S30][S24]. |
| Executes | Runs "50+ static analyzers, linters and SAST tools" in sandboxed environments [S27][S26]. Executing project code or tests is not documented [S26][S27]. |
| Context beyond the diff | "Agentic exploration", a code graph (definitions, references, co-changed files), multi-repo analysis for cross-repo breaking changes, MCP servers, web search, past PRs [S27][S30]. |
| Output | Walkthrough comment (summary, Mermaid sequence diagrams, 1 to 5 review-effort score, related PRs, linked-issue assessment, Merge Risk rating), inline comments, and pre-merge checks [S25][S28]. Coverage claims: runtime errors, races, logic flaws, performance, maintainability, architecture [S29]. |
| Missing context | Linked issue verdicts: Addressed / Not addressed / Unclear [S24]. Pre-merge checks can return Inconclusive when "information was insufficient", which does not block [S28]. No linked issue: no assessment runs [S24]. |

Built-in pre-merge checks include **Issue Assessment** ("addresses its linked issues without out-of-scope changes"); custom checks are natural-language instructions that run in a read-only sandbox with the diff, linked issues and MCP context, in off / warning / error modes [S28].

#### GitHub Copilot code review

| Field | Finding |
| --- | --- |
| Reads | The PR changes; "analyzes your entire repository to better understand the context" [S32]. Excludes some files such as dependency manifests [S32]. |
| Reference | `.github/copilot-instructions.md`, path-specific `.instructions.md`, `AGENTS.md`, and also `CLAUDE.md`, `GEMINI.md`, `REVIEW.md`, read from the **head** branch [S33]. PR descriptions and linked issues are not documented as inputs, except that identifiers in the description can steer MCP lookups [S33][S32]. |
| Executes | Static analysis: CodeQL (on by default), ESLint and PMD, toggled by a repository rule [S35]. Agentic capabilities run on GitHub Actions [S32][S36]. The GitHub and Playwright MCP servers are on by default, but what Playwright is used for in review is not documented [S32]. |
| Context beyond the diff | Agentic tool calling for "relevant code, directory structure, and references" [S36][S34]; skills and MCP when relevant [S33]. |
| Output | A "Comment" review with an approval assessment in the overview; approving is opt-in and off by default; suggested fixes can be handed to the Copilot coding agent [S32][S33][S34]. Lite and Balanced effort levels [S32]. |
| Missing context | Not documented. If Actions is unavailable, reviews still run without the agentic features [S32]. |

### E. Other agentic review skills

#### BMAD-METHOD `bmad-code-review` (commit 61e01f8)

| Field | Finding |
| --- | --- |
| Reads | A diff written to a temp file (PR, branch from merge-base, commit range, staged, uncommitted, or a plan baseline); warns and offers chunking above about 3,000 lines [S41]. |
| Reference | The ticket's Description, Requirements and Acceptance Criteria, or the plan's intent section, or the user's own words; `AGENTS.md` / `CLAUDE.md` in the quick lens [S41]. |
| Executes | No. Every lens is "Review by inspection only. Do not modify code, run builds or tests" [S41]. |
| Context beyond the diff | Per lens, deliberately limited. Lenses are context-free subagents that receive file paths, never pasted diff text [S41]. |
| Output | Lens findings triaged, presented and optionally applied or handed off [S41]. |
| Missing context | Interactive mode asks for a plan and does not "assume no-plan just because none was given"; otherwise **no-plan mode**, in which "triage cannot tell a deliberate choice from a mistake" and lists possible fixes with a recommendation instead of choosing [S41][S42]. Lenses whose `when` condition fails are skipped and announced [S41]. Without subagents, it writes standalone prompts and asks the user to run them in another session, "ideally a different LLM" [S41]. |

The thorough lens set [S41]:

- **Blind Hunter**: diff only, must find at least `min(floor(sqrt(kB) + 1), 10)` issues, "Look for what's missing, not only what's wrong".
- **Edge Case Hunter**: "pure path tracer" that walks every branch and boundary reachable from changed lines, including implicit enum members, handle lifetimes, and every new call site against the callee's declaration; then a deletion check; then a **claims check** that reads the author's narrative only after tracing and tries to falsify each claim.
- **Verification Gap Reviewer**: finds "behavior this change altered that could break later without any test failing" (regression, missing-adoption, broken-verification and stale-verification gaps), requiring a named regression and reading the actual tests.
- **Intent Alignment Auditor**: lists the defensible readings of the intent, which reading the diff implements, and "which surface the intent's expectations live at versus which surface the diff's changes and its tests exercise".

Its docs say "without intent, the reviewers can only judge the diff against itself", and that non-trivial findings on a third review pass "usually mean something is wrong upstream of this change" [S42].

### F. Tools that review specs or PRDs before code exists

#### GitHub Spec Kit

- **`clarify`**: scans the active spec against a taxonomy (functional scope, data model, UX flow, non-functional attributes, integrations, edge cases and failure handling, constraints, terminology, completion signals, placeholders), marks each Clear / Partial / Missing, asks at most 5 questions, and writes answers back into the spec. Meant to finish before planning; skipping it must warn of rework risk [S39].
- **`analyze`**: strictly read-only cross-check of `spec.md`, `plan.md`, `tasks.md` and the constitution after task generation; passes for duplication, ambiguity, underspecification, constitution alignment, coverage gaps (requirements with no task, tasks with no requirement) and inconsistency; CRITICAL to LOW severity; a findings table capped at 50 rows plus coverage metrics. Aborts if a required artifact is missing [S37].
- **`checklist`**: "unit tests for requirements writing": items test completeness, clarity, consistency, measurability and edge-case coverage of the *requirements*; it is explicitly not for verifying behaviour [S38].

#### Kiro

Specs are `requirements.md` (or `bugfix.md`), `design.md` and `tasks.md`. **Analyze Requirements** is described as catching "inconsistencies, ambiguities, and gaps in your requirements before design"; a Review button allows comments on passages; "Correctness (property-based testing)" is listed as an IDE capability without detail of how properties link to requirements. Checking the implementation against the spec is not stated [S40].

#### BMAD PRD, architecture and ticket validation

- **PRD rubric**: a validator subagent judges seven dimensions (decision-readiness, substance over theater, strategic coherence, done-ness clarity, scope honesty, downstream usability, shape fit) as strong / adequate / thin / broken, with critical-to-low findings; "Done-ness clarity" asks for at least one testable consequence per functional requirement and to "flag every" vague phrase such as "handles X gracefully" [S43].
- **Architecture reviewer gate**: a deterministic lint first, then parallel independent reviewers, because "a fresh reviewer finds the divergences the author talks past"; a silent dimension (deployment, environments, operations) "is a finding" [S44].
- **Ticket validation checks**: every requirement covered by a ticket, each ticket has a `verify` "a non-builder can run", dependency and collision checks across tickets [S45].

#### CodeRabbit Issue Planner

From an issue, researches the codebase and past issues, PRs and docs, and produces an editable "Coding Plan" that "you and your team can review and refine ... before any code is written", correcting the assumptions it made. An explicit gap or ambiguity check of the issue is not described [S31].

---

## Cross-cutting observations against the thesis

The user's thesis: reviewers catch obvious problems, are too focused on the diff, miss the overall picture, and struggle when context is missing.

**Diff focus.** Confirmed by design in several sources. Claude Code `low` effort forbids full-file reads [S11]; the marketplace `code-review` plugin's bug agent should "avoid reading extra context beyond the changes" [S19]; BMAD's Edge Case Hunter should "Ignore the rest of the codebase unless the provided content explicitly references external functions" [S41]; Matt Pocock's reviewer reads only the diff, standards and spec [S1]. Diff-plus approaches widen to callers, history and repo search [S11][S19][S23][S27][S36], but the unit of judgement stays the change.

**Overall picture.** Partially covered by reading: Claude Code's altitude angle [S11], CodeRabbit's sequence diagrams, multi-repo analysis and architecture suggestions [S25][S29][S30], Matt Pocock's end-of-branch pass and `improve-codebase-architecture` for whole-codebase drift [S2]. **Analysis:** no surveyed tool reviews a change against the system's intended behaviour as a whole (for example, the glossary, ADRs and other features it must compose with). Matt Pocock's `tdd` and `to-spec` read `GLOSSARY.md` and ADRs, but his `code-review` does not [S5][S6][S1].

**Missing context.** Three behaviours exist: (a) proceed silently on the diff (Claude Code bundled and managed, Bugbot, Copilot) [S10][S13][S22][S33]; (b) ask, then degrade visibly (Matt Pocock, BMAD, in-house `verify`) [S1][S41][S8]; (c) return an explicit uncertain verdict (CodeRabbit `Unclear` / `Inconclusive`) [S24][S28]. Only Claude Code's bundled review discloses a degraded *method* (no subagents) [S11]; none discloses a degraded *reference* except Matt Pocock ("no spec available") and BMAD (skipped lens announced) [S1][S41].

**Anchoring and independence.** Sources that address it: Matt Pocock recommends a fresh session [S2]; Claude Code's `/code-review` runs as a forked subagent with its own context [S10]; BMAD lenses are context-free and the claims file is hidden until tracing is done [S41]; `claude-security` uses three refutation voters with arithmetic "done outside every model" [S21]; Bugbot originally ran eight passes with shuffled diff order and majority vote [S23].

**Review versus verification.** Most "verify" steps in reviewers are a second *reading* to filter false positives (Claude Code [S11][S13], `claude-security` [S21], the marketplace plugin's confidence scoring [S19]). Only ultrareview claims reproduction [S12], and only `/verify` / in-house `verify` produce runtime evidence at the user's surface [S16][S8]. BMAD's Verification Gap lens reviews whether verification *exists* (tests that would fail) without running anything [S41].

---

## Coverage matrix

Legend: **Y** = an explicit, documented aim; **P** = partial, indirect, or only via user-written rules; **-** = not covered or not documented. `R` marks coverage by review (reading), `V` by verification (execution).

| Tool | Spec gaps | Spec alignment | Maintainability | Emergent edge cases | Trust-boundary bypass | User-perspective behaviour |
| --- | --- | --- | --- | --- | --- | --- |
| Matt Pocock `code-review` [S1][S2] | - | Y (R) | Y (R): standards + Fowler smells | - (defers bug hunting) | - | - |
| In-house `verify` [S8] | - | P (V): claim vs diff vs runtime | - | Y (V): probes at the surface | P (V): only if the change is a gate | Y (V) |
| Claude Code `/code-review` [S10][S11] | - | - | Y (R) at medium+: cleanup, altitude, CLAUDE.md | Y (R): correctness angles, cross-file tracer | P (R): language pitfalls such as SQL injection | - |
| ultrareview [S12] | - | P (R): free-text note only | - | Y (R, reproduced) | P (R) | - |
| Claude managed Code Review [S13][S14] | - | - | P (R): only via REVIEW.md / CLAUDE.md | Y (R) | P (R): "security vulnerabilities" named | - |
| `/simplify` [S11] | - | - | Y (R, applies fixes) | - | - | - |
| `/security-review` [S17][S18] | - | - | - | P (R): TOCTOU, races (theoretical races excluded) | Y (R): authz bypass, privilege escalation | - |
| `claude-security` plugin [S21] | - | - | - | - | Y (R): threat model, 3-vote refutation | - |
| `/verify` bundled [S16] | - | P (V) | - | Y (V) | - | Y (V) |
| Marketplace `code-review` plugin [S19] | - | - | P (R): only CLAUDE.md rules | P (R): "obvious bugs", history | - | - |
| `pr-review-toolkit` [S20] | - | - | Y (R): types, comments, simplifier | P (R): silent failures, test gaps | - | - |
| Cursor Bugbot [S22][S23] | - | P (R): only via rules | P (R): via rules | Y (R) | P (R): not a documented focus | - |
| CodeRabbit [S24][S26][S27][S28][S29] | P (R): `Unclear` verdict exposes vague issues | Y (R): issue title/description | Y (R) | Y (R) + static tools (V) | P (R) + SAST tools (V) | - |
| Copilot code review [S32][S33][S35] | - | P (R): only via MCP identifiers | P (R): "style inconsistencies" | Y (R) + CodeQL/ESLint/PMD (V) | P (R) + CodeQL (V) | - (Playwright MCP use undocumented) |
| BMAD `bmad-code-review` [S41][S42] | P (R): intent readings enumerated | Y (R): Intent Alignment Auditor | P (R): Blind Hunter | Y (R): Edge Case Hunter, Verification Gap | - | - |
| Spec Kit `clarify` / `analyze` / `checklist` [S37][S38][S39] | Y (R) | P (R): spec to plan to tasks, not code | - | P (R): spec-level edge cases | - | - (excluded by design) |
| Kiro specs [S40] | Y (R): Analyze Requirements | - (not stated) | - | P: property-based testing listed, not detailed | - | - |
| BMAD PRD / architecture / ticket validation [S43][S44][S45] | Y (R) | P (R): ticket coverage of requirements | - | - | P (R): optional security lens at the gate | - |
| CodeRabbit Issue Planner [S31] | P (R, human) | - | - | - | - | - |

**Reading the matrix (Analysis).**

- **Spec gaps** are covered only by pre-code spec tools; no PR reviewer looks back at whether the spec itself was wrong, apart from CodeRabbit's `Unclear` verdict and BMAD's enumeration of intent readings.
- **Spec alignment** by review exists in three tools; none verifies it by execution except our own `verify`, which checks a *claim*, not a spec.
- **Maintainability** is the best-covered concern, by review only.
- **Emergent edge cases** are widely hunted by reading; only `verify` / `/verify` find them by execution, and only ultrareview claims to reproduce what reading found.
- **Trust-boundary bypass** is covered by reading and refutation; the glossary's "attempting to exploit it" has no surveyed implementation.
- **User-perspective behaviour** is covered only by `/verify` and our in-house `verify`, and only at the change checkpoint.

---

## Unverified or open points

- How ultrareview "independently reproduced" findings: whether it executes code is not stated [S12].
- What Copilot code review does with the Playwright MCP server, which is on by default [S32].
- Whether CodeRabbit's "Verification" agent executes anything, and whether it runs project tests in its sandbox [S27][S26].
- How Kiro's property-based correctness checks relate to requirements, and whether Kiro checks code against the spec [S40].
- Claude Code bundled prompt text was read from the local v2.1.310 binary [S11]; it is not published and may change between versions.
- `GLOSSARY.md` with the `## Assurance` section exists in the main checkout but not yet on this branch's base commit [S46].

---

## Sources

Local files are cited by absolute path. GitHub sources are pinned to a commit where one was resolved. Web pages were read on 2026-10-26.

- **[S1]** Matt Pocock, `code-review` SKILL.md, mattpocock-skills 1.3.1. `~/.claude/plugins/cache/claude-plugins-official/mattpocock-skills/1.3.1/skills/engineering/code-review/SKILL.md`
- **[S2]** Matt Pocock, `code-review` docs page. `~/.claude/plugins/cache/claude-plugins-official/mattpocock-skills/1.3.1/docs/engineering/code-review.md`
- **[S3]** Matt Pocock, `implement` SKILL.md. `.../mattpocock-skills/1.3.1/skills/engineering/implement/SKILL.md`
- **[S4]** Matt Pocock, `implement-spec` SKILL.md. `.../mattpocock-skills/1.3.1/skills/engineering/implement-spec/SKILL.md`
- **[S5]** Matt Pocock, `tdd` SKILL.md. `.../mattpocock-skills/1.3.1/skills/engineering/tdd/SKILL.md`
- **[S6]** Matt Pocock, `to-spec` SKILL.md. `.../mattpocock-skills/1.3.1/skills/engineering/to-spec/SKILL.md`
- **[S7]** Matt Pocock, `grill-with-docs` SKILL.md. `.../mattpocock-skills/1.3.1/skills/engineering/grill-with-docs/SKILL.md`
- **[S8]** This repo, `under-construction/verify/SKILL.md`, `BRIEF.md`, `STATUS.md` (commit cd07773).
- **[S9]** Claude Code docs, Commands. https://code.claude.com/docs/en/commands
- **[S10]** Claude Code docs, Review locally with /code-review. https://code.claude.com/docs/en/code-review-local
- **[S11]** Claude Code v2.1.310 bundled `/code-review` and `/simplify` prompt behaviour, observed in the locally installed Claude Code 2.1.310 program. Not published; paraphrased, not quoted.
- **[S12]** Claude Code docs, Find bugs with ultrareview. https://code.claude.com/docs/en/ultrareview
- **[S13]** Claude Code docs, Code Review. https://code.claude.com/docs/en/code-review
- **[S14]** Claude Code docs, Customize Code Review. https://code.claude.com/docs/en/code-review-customize
- **[S15]** Claude Code docs, Read and request reviews on a pull request. https://code.claude.com/docs/en/code-review-pull-requests
- **[S16]** Claude Code docs, Skills: Run and verify your app. https://code.claude.com/docs/en/skills#run-and-verify-your-app
- **[S17]** Anthropic, claude-code-security-review README. https://github.com/anthropics/claude-code-security-review
- **[S18]** Anthropic, `security-review.md` command prompt. https://github.com/anthropics/claude-code-security-review/blob/main/.claude/commands/security-review.md
- **[S19]** Anthropic claude-plugins-official, `code-review` plugin command and README. `~/.claude/plugins/marketplaces/claude-plugins-official/plugins/code-review/`
- **[S20]** Anthropic claude-plugins-official, `pr-review-toolkit` `review-pr.md` and agents. `~/.claude/plugins/marketplaces/claude-plugins-official/plugins/pr-review-toolkit/`
- **[S21]** Anthropic claude-plugins-official, `claude-security` 0.12.0 README and `agents/scan-verifier.md`. `~/.claude/plugins/marketplaces/claude-plugins-official/plugins/claude-security/`
- **[S22]** Cursor docs, Bugbot. https://cursor.com/docs/bugbot
- **[S23]** Cursor blog, Building a better Bugbot. https://cursor.com/blog/building-bugbot
- **[S24]** CodeRabbit docs, Linked issues. https://docs.coderabbit.ai/guides/linked-issues (same content at https://docs.coderabbit.ai/issues/pr-validation.md)
- **[S25]** CodeRabbit docs, PR Walkthroughs. https://docs.coderabbit.ai/pr-reviews/walkthroughs
- **[S26]** CodeRabbit docs, Tools. https://docs.coderabbit.ai/tools
- **[S27]** CodeRabbit docs, Architecture. https://docs.coderabbit.ai/overview/architecture.md
- **[S28]** CodeRabbit docs, Built-in Pre-Merge Checks. https://docs.coderabbit.ai/pr-reviews/pre-merge-checks.md
- **[S29]** CodeRabbit docs, Pull Request Reviews. https://docs.coderabbit.ai/overview/pull-request-review.md
- **[S30]** CodeRabbit docs index entries for Knowledge Base, Code Guidelines, Multi-Repo Analysis, MCP Servers, Web Search. https://docs.coderabbit.ai/llms.txt and https://docs.coderabbit.ai/knowledge-base/index.md
- **[S31]** CodeRabbit blog, Issue Planner. https://coderabbit.ai/blog/issue-planner-collaborative-planning-for-teams-with-ai-agents
- **[S32]** GitHub docs, About Copilot code review. https://docs.github.com/en/copilot/concepts/agents/code-review
- **[S33]** GitHub docs, Using Copilot code review. https://docs.github.com/en/copilot/how-tos/use-copilot-agents/request-a-code-review/use-code-review
- **[S34]** GitHub changelog, 2025-10-28, New public preview features in Copilot code review. https://github.blog/changelog/2025-10-28-new-public-preview-features-in-copilot-code-review-ai-reviews-that-see-the-full-picture/
- **[S35]** GitHub changelog, 2025-11-20, Linter integration with Copilot code review. https://github.blog/changelog/2025-11-20-linter-integration-with-copilot-code-review-now-in-public-preview/
- **[S36]** GitHub changelog, 2026-03-05, Copilot code review now runs on an agentic architecture. https://github.blog/changelog/2026-03-05-copilot-code-review-now-runs-on-an-agentic-architecture/
- **[S37]** GitHub Spec Kit, `templates/commands/analyze.md`. https://github.com/github/spec-kit/blob/main/templates/commands/analyze.md
- **[S38]** GitHub Spec Kit, `templates/commands/checklist.md`. https://github.com/github/spec-kit/blob/main/templates/commands/checklist.md
- **[S39]** GitHub Spec Kit, `templates/commands/clarify.md`. https://github.com/github/spec-kit/blob/main/templates/commands/clarify.md
- **[S40]** Kiro docs, Specs. https://kiro.dev/docs/specs/
- **[S41]** BMAD-METHOD `skills/bmad-code-review/` (`customize.toml`, `step-01-gather-context.md`, `step-02-review.md`, `review-prompts/edge-case-hunter.md`, `review-prompts/verification-gap.md`, `references/claims-check.md`) at commit 61e01f82644c4bb533750cfa0d6d61ab61d2cc9b. https://github.com/bmad-code-org/BMAD-METHOD/tree/61e01f82644c4bb533750cfa0d6d61ab61d2cc9b/skills/bmad-code-review
- **[S42]** BMAD-METHOD `docs/build/review-a-change.md` at 61e01f8. https://github.com/bmad-code-org/BMAD-METHOD/blob/61e01f82644c4bb533750cfa0d6d61ab61d2cc9b/docs/build/review-a-change.md
- **[S43]** BMAD-METHOD `skills/bmad-prd/assets/prd-validation-checklist.md` and `skills/bmad-prd/references/validate.md` at 61e01f8. https://github.com/bmad-code-org/BMAD-METHOD/tree/61e01f82644c4bb533750cfa0d6d61ab61d2cc9b/skills/bmad-prd
- **[S44]** BMAD-METHOD `skills/bmad-architecture/references/reviewer-gate.md` at 61e01f8. https://github.com/bmad-code-org/BMAD-METHOD/blob/61e01f82644c4bb533750cfa0d6d61ab61d2cc9b/skills/bmad-architecture/references/reviewer-gate.md
- **[S45]** BMAD-METHOD `skills/bmad-agent-po/references/validate-checks.md` at 61e01f8. https://github.com/bmad-code-org/BMAD-METHOD/blob/61e01f82644c4bb533750cfa0d6d61ab61d2cc9b/skills/bmad-agent-po/references/validate-checks.md
- **[S46]** This repo, `GLOSSARY.md` `## Assurance` section, at the repo root.
