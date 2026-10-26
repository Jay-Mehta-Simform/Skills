# Techniques for verifying trust boundaries

Research for issue #3, "Techniques for verifying trust boundaries". Sources were read on
2026-10-26. Each claim cites the source that owns it; numbered references are listed at the end.
Passages marked **Inference** are this document's own reasoning from the sources, not claims made
by them.

Vocabulary follows the `## Assurance` section of `GLOSSARY.md`: **review** judges by reading
against a reference, **verification** produces evidence by executing something, a **concern** is
one thing assurance looks for, such as trust-boundary bypass.

## Question

How do practitioners and agent tools find a system's trust boundaries and verify that they hold?
The motivating case: a client and server built together, where the server can be reached without
the client, bypassing client-side validation, auth, rate limits, ordering or other rules that
protect data integrity. Which techniques can an agent apply generically from a codebase and a
running app, what must a project tell the agent for the rest, and what safety limits apply?

## Short answer

- The motivating case is a named, long-standing weakness class: CWE-602 "Client-Side Enforcement
  of Server-Side Security" [24]. OWASP ASVS 5.0 makes server-side enforcement a Level 1
  requirement for both input validation (2.2.2) and authorization (8.3.1) [1][2], and requires
  step order (2.3.1), limits (2.3.2) and anti-automation (2.4.1) to be enforced by the
  application [1].
- **Finding boundaries** has two practitioner traditions: threat modeling (data-flow diagrams with
  explicit trust boundaries, then STRIDE or attack trees) [20][26][27][29], and attack-surface
  analysis (enumerate every entry point, from source and from traffic) [18][12][13]. Source-code
  endpoint extractors such as OWASP Noir list routes "that no current client calls" [13], which
  is exactly the surface the motivating case is about.
- **Verifying boundaries** is mostly a small set of mechanical probes against the running server,
  bypassing the client: replay a request with tampered, removed or extra fields [6][33]; replay it
  as another user, a lower role, or no user [11][36][37]; invoke later workflow steps without
  earlier ones [10][33]; repeat a once-only action [9]; fire concurrent requests at a limit [34].
- **The mechanics are generic; the oracle is not.** An agent can enumerate endpoints, find guards
  in handlers, extract client-side constraints, and replay requests without project input. It
  cannot know, without being told, which roles may do what, which limits are intended, which
  step order is required, or which flows are sensitive. OWASP puts these in project documentation
  (ASVS 2.1.1 to 2.1.3, 8.1.1, 8.1.2) [1][2], and WSTG says business logic abuse testing relies on
  "knowledge of the complete business process and its rules" [5].
- **Current agent tools split along the review/verification line.** Claude Code's
  `/security-review`, the security guidance plugin and the Claude Security plugin read source and
  do not exercise a running app [39][41][42]. `/security-review` is limited to the diff, tells the
  model not to run commands, and excludes rate limiting by design [39]. Open-source agentic
  pentesters (Shannon, Strix) do execute against a running app and require proof of exploit, but
  carry strong warnings about authorization, production use and state mutation [44][45].
- **Safety**: run only against local or disposable environments the user owns, with synthetic
  data, network egress restricted to the local target, bounded request volumes, no irreversible or
  externally visible side effects, and human review of findings [44][45][47][49][43].

## 1. The weakness class behind the motivating case

| Rule the client enforces | Where OWASP / MITRE require server-side enforcement |
|---|---|
| Input validation (types, ranges, allowed values, field relationships) | ASVS 2.2.1, 2.2.2 (L1: "enforce input validation at a trusted service layer"), 2.2.3 [1]; WSTG-BUSL-01 [6]; Input Validation Cheat Sheet: "Validate on the server even when the browser checks the same fields" [17] |
| Who may call a function, see an object, or read/write a field | ASVS 8.2.1 (function), 8.2.2 (data, IDOR/BOLA), 8.2.3 (field, BOPLA), 8.3.1 (L1: enforce "at a trusted service layer", not via client-side controls) [2]; Authorization Cheat Sheet: "Developers must never rely on client-side access control checks" [16] |
| Step order in a multi-step flow | ASVS 2.3.1 (L1: process flows "in the expected sequential step order") [1]; CWE-841 Improper Enforcement of Behavioral Workflow [25]; WSTG-BUSL-06 [10] |
| Per-user and global limits, once-only actions | ASVS 2.1.3, 2.3.2 [1]; WSTG-BUSL-05 [9] |
| Rate limits, anti-automation | ASVS 2.4.1 (L2), 2.4.2 (L3) [1]; API4:2023 Unrestricted Resource Consumption, API6:2023 Unrestricted Access to Sensitive Business Flows [22][23] |
| Scarce resources and check-then-act | ASVS 2.3.4 (locking for limited-quantity resources), 15.4.2 (TOCTOU) [1][3] |
| Only fields the form shows | ASVS 15.3.3 mass assignment countermeasures [3]; Mass Assignment Cheat Sheet [21]; API3:2023 [22] |

CWE-602 states the pattern directly: "The product is composed of a server that relies on the
client to implement a mechanism that is intended to protect the server", and its mitigation is to
ensure client-side checks "are duplicated on the server side" [24]. PortSwigger names the root
cause as the assumption "that users will only interact with the application via the provided web
interface" [33]. WSTG-BUSL-02 describes the attack as using an intercepting proxy "to circumvent
the frontend GUI application to directly submit information for backend processing" [7].

The same rule applies in the other direction. The Input Validation Cheat Sheet says to validate
data "from internal APIs, partner feeds, queues, and stored records when it crosses a trust
boundary" [17], and API10:2023 notes developers tend to trust third-party API data more than user
input [22]. A trust boundary is therefore not only "browser to server".

## 2. Finding the boundaries

### 2.1 Threat modeling

- The Threat Modeling Manifesto frames the work as four questions: "What are we working on?",
  "What can go wrong?", "What are we going to do about it?", "Did we do a good enough job?" [28].
  It favours "Continuous refinement" and analysis that follows "design changes in iterations that
  are each scoped to manageable portions of the system" [28], which suits per-change checkpoints.
- The OWASP Threat Modeling Cheat Sheet calls data-flow diagrams "arguably the most common
  approach" to the first question and says the model must give "a clear view of trust boundaries,
  data flows, data stores, processes, and the external entities" [20]. Microsoft's Threat
  Modeling Tool uses the same element set (process, external interactor, data store, data flow,
  and "Trust line/Border boundary") [27].
- STRIDE (Spoofing, Tampering, Repudiation, Information disclosure, Denial of service, Elevation
  of privilege) is applied to the components, flows and boundaries of that model [20][26]. The
  motivating case lands mainly in Tampering ("unauthorized changes made to persistent data") and
  Elevation of Privilege [26].
- Attack trees (Schneier, 1999) put the attacker's goal at the root, with OR nodes as
  alternatives and AND nodes as required steps; leaves can be marked possible or impossible and
  costed [29]. The Threat Modeling Cheat Sheet recommends them for "A high-value attacker goal or
  multi-step attack" [20], which fits workflow bypass.
- Threat models can be code. OWASP pytm defines `Boundary`, `Actor`, `Server` and `Dataflow`
  objects in Python and generates a DFD, a sequence diagram and a threat report [30].

**Inference.** An agent can draft the "what are we working on" model from a codebase: the client
apps, the server entry points, the data stores, and outbound calls are all visible in code, and
pytm shows the model can be expressed as code an agent writes. What an agent cannot settle alone
is which data matters and which rules the business depends on; the cheat sheet expects threat
identification to be done "with the team" [20].

### 2.2 Attack-surface enumeration

The OWASP Attack Surface Analysis Cheat Sheet defines the attack surface as "the sum of all paths
for data/commands into and out of the application" plus "the code that protects these paths
(including resource connection and authentication, authorization, activity logging, data
validation and encoding)" [18]. It says to overlay roles, and to focus on "the two extremes:
unauthenticated, anonymous users and highly privileged admin users" [18]. It lists ways to build
the map: read source for entry points, crawl the running app with a dynamic scanner, and walk the
main use cases while following data through validation and storage [18].

From the running app, WSTG-INFO-06 has the tester proxy every request and record, per request,
the parameters, method, whether it is authenticated, "if it's part of a multi-step process", and
hidden fields that "usually contain sensitive information such as state information, quantity of
items, the price of items" [12]. WSTG-APIT-01 adds well-known documentation paths (`/openapi.json`,
`/swagger`), endpoint extraction from client JavaScript bundles (regex and AST tools such as
LinkFinder and jsluice), and active fuzzing for unlisted routes [13].

From source code, WSTG points to two extractors:

- **OWASP Attack Surface Detector** "investigates the source code and uncovers the endpoints of a
  web application, the parameters these endpoints accept", including "unlinked endpoints that a
  spider wouldn't be able to find, as well as optional parameters that are completely unused in
  the client-side code" [12].
- **OWASP Noir** "parses the routing code of many web frameworks and lists every endpoint with its
  methods and parameters, including internal or deprecated APIs that no current client calls",
  and can export them as OpenAPI for import into ZAP or Burp [13]. Its README claims coverage of
  261 frameworks, an LLM fallback for unsupported routing, and an `--ai-context` flag that attaches
  per-endpoint "guards, sinks, validators, and signals" for LLM auditors [32].

**Inference.** For the motivating case, the most direct generic check is a set difference:
*endpoints and parameters the server accepts* minus *endpoints and parameters the client sends*.
Everything in the difference is reachable only by bypassing the client, so no client-side rule
can be protecting it. API9:2023 Improper Inventory Management names the production version of
this problem (deprecated versions and exposed debug endpoints) [22].

### 2.3 Classifying entry points by enforcement

Trail of Bits' `entry-point-analyzer` skill (for smart contracts) shows the agent-skill version
of this step: find state-changing entry points, exclude read-only ones, and classify each as
Public, Role-Restricted, Review Required (ambiguous checks) or Contract-Only, reporting a table
with `file:line` references [48]. Shannon's open-source edition describes a similar "agentic
security code analysis" phase that "maps architecture, trust boundaries, and data flows" before
exploitation [44].

**Inference.** The same classification transfers to web servers: for each state-changing route,
record which guards run before the handler touches data (authentication, authorization on the
function, ownership check on the object, field allowlist, validation schema, rate limiter, state
check). The "Review Required" bucket is where an agent should stop and verify by execution or ask.

## 3. Verifying that the boundaries hold

Each technique below is a verification in the glossary's sense: it sends requests to a running
server without going through the client and records what the server does.

| # | Technique | What it proves | Primary sources |
|---|---|---|---|
| T1 | **Constraint replay.** For each parameter, replay a captured request with values the client would never send: out of range, negative, zero, outside the allowed set, wrong type, over-length, inconsistent with other fields. Compare response, stored data, and later effects. | Server-side validation exists for each client-side rule | WSTG-BUSL-01 "Parameter-Based Test Cases" [6]; ASVS 2.2.1 to 2.2.3 [1]; NoTamper [35] |
| T2 | **Parameter removal and addition.** Remove one parameter at a time (name and value); add fields the client never sends (`role`, `price`, `ownerId`, `status`); repeat a parameter. | Required inputs are required server-side; no mass assignment | PortSwigger [33]; WSTG-BUSL-01 [6]; Mass Assignment Cheat Sheet [21]; ASVS 15.3.3 [3] |
| T3 | **Direct request without session.** Request every enumerated endpoint with no credentials ("forced browsing"). | Authentication is enforced on every route, not only those the UI links to | WSTG-ATHZ-02 [11]; ZAP Access Control Testing [37] |
| T4 | **Identity swap.** Replay each request under a second user of the same role (horizontal) and a lower role (vertical); swap object IDs between users and tenants; try other HTTP methods on the same path. | Function-, object- and field-level authorization | WSTG-ATHZ-02 steps 1 to 4 [11]; WSTG-APIT-04 [14]; ASVS 8.2.1 to 8.2.3, 8.4.1 [2]; Autorize [36] |
| T5 | **Step skipping and reordering.** Capture each step of a multi-step flow; call later steps without earlier ones; reorder; replay state IDs; set status/phase parameters to future or invalid values. | Workflow state is enforced server-side | WSTG-BUSL-06 Method 3 [10]; ASVS 2.3.1 [1]; CWE-841 [25]; PortSwigger [33] |
| T6 | **Repeat once-only actions.** Re-submit a discount, redemption, vote, or approval; go back and forth through the flow. | Per-user and per-transaction limits | WSTG-BUSL-05 [9]; ASVS 2.3.2 [1] |
| T7 | **Concurrent limit overrun.** Send a small burst of identical requests at the same instant against a limit or a scarce resource. | Check-then-act is atomic | Kettle, single-packet attack, "predict, probe, prove" [34]; ASVS 2.3.4, 15.4.2 [1][3] |
| T8 | **Volume.** Send requests directly at machine speed to a function the UI throttles or debounces. | Rate limits and anti-automation live on the server | ASVS 2.4.1, 2.4.2 [1]; API4 and API6:2023 [22][23] |
| T9 | **Timing and abandonment.** Hold a reservation or quote open and complete it late. | Timeouts and price/stock re-checks | WSTG-BUSL-04 [8] |
| T10 | **Executable authorization matrix.** Encode role x service (x data) as a file, generate one integration test per cell, assert allowed/denied status codes. | Regression protection for T3 and T4 on every release | Authorization Testing Automation Cheat Sheet [19] |

Notes on the evidence:

- **Baselines and deny fingerprints.** Identity-swap tools compare each replay with the
  legitimate response. Autorize labels results "Bypassed!", "Enforced!" or "Is enforced???", and
  needs a configured fingerprint (status, header, body regex, length) when it cannot tell a denial
  from success [36]. WSTG-ATHZ-02 shows the same pattern with three identities (victim baseline,
  other user, anonymous) [11]. An agent needs the same: a known-good response and a known-denied
  response for each endpoint.
- **Check the side effects, not only the status.** WSTG-BUSL-01 says to compare "the response,
  the stored data, and any later behavior (emails, background jobs, other users' views)" and to
  record which variations were accepted, "because the impact depends on how the application uses
  the value afterwards" [6]. A `200` with nothing persisted and a `400` after a partial write are
  both misleading if only the status is read.
- **Client code as the oracle.** NoTamper (CCS 2010) is titled "automatic blackbox detection of
  parameter tampering opportunities in web applications" [35]; its premise, as summarized in
  bibliographic listings, is that tampering is dangerous where the server does not replicate the
  validation performed by client-side form code. **Inference:** this is the most useful generic
  idea for an agent working on a co-built client and server. The client already encodes the
  intended rules (form constraints, schemas, disabled buttons, step guards in routing), so the
  agent can extract them and use each one as a T1, T2 or T5 probe without the project writing the
  rules down a second time. The abstract itself could not be retrieved, so details of the paper's
  method are not relied on here.
- **Scanners do not find these unaided.** WSTG says business logic flaws "cannot be detected by a
  vulnerability scanner" and that tools "have no means of detecting if a user is able to
  circumvent the business process flow through editing parameters, predicting resource names or
  escalating privileges" [5].

## 4. What current agent tools do

| Tool | Kind | Executes against a running app? | Relevant scope and limits |
|---|---|---|---|
| Claude Code `/security-review` | Review | No. The prompt says "Do not use the bash tool or write to any files" and "just read the code" [39] | Diff only ("focus ONLY on security implications newly added by this PR. Do not comment on existing security concerns"); covers "Authorization logic bypasses" and privilege escalation; hard-excludes "Rate limiting concerns" and DoS; precedent 8 treats missing checks in client-side JS/TS as non-issues because "the backend is responsible for validating" [39]. The GitHub Action is "not hardened against prompt injection attacks" [38] |
| Claude Code security guidance plugin | Review | No | Per-edit pattern match, end-of-turn diff review, and commit review; end-of-turn review targets "Authorization bypass" and IDOR. Project rules go in `.claude/claude-security-guidance.md`, for example "All routes under `/admin` must call `require_role("admin")` before any database read". Findings do not block writes [41] |
| Claude Code Claude Security plugin | Review | No. Reviews "read the source code in your checkout, not a running site or deployed service" [41] | Agents "map your architecture, build a threat model, hunt for vulnerabilities, and independently review every finding"; scans are nondeterministic [42] |
| Trail of Bits skills | Review | No (static) | `entry-point-analyzer` (classify entry points by access level), `spec-to-code-compliance` (split docs into requirements, check each against code, try to refute each divergence) [48] |
| OWASP Noir | Enumeration | No (static) | Endpoint and parameter inventory from source, OpenAPI export, per-endpoint guard context for LLMs [31][32] |
| Shannon (KeygraphHQ) | Review + verification | Yes, white-box: needs source and a running app | Tests "broken authentication, and broken authorization"; "No exploit, no report"; "Do not run Shannon against production systems"; it "can create users, submit forms, mutate application state, trigger outbound requests" [44] |
| Strix | Verification (optionally with source) | Yes: Caido proxy, browser, terminal, Python sandbox | Lists access control ("IDOR, privilege escalation, auth bypass") and business logic ("Race conditions, payment manipulation, workflow bypass"); claims PoC validation; "Authorized use only" [45] |
| PentestGPT | Verification | Yes | Research agent (USENIX Security 2024) oriented to CTF and pentest stages; "authorized security testing only" [46] |
| CAI (Alias Robotics) | Framework | Yes | Archived; "Run it only in isolated environments, against systems you are explicitly authorised to test" [47] |
| Burp Autorize, ZAP Access Control Testing | Verification (non-agentic, drivable) | Yes | Multi-identity replay with enforcement detection [36]; per-user access rules then "trying to access every URL of the web-app from the perspective of every user" [37] |

**Inference: gaps relative to the motivating case.**

1. The built-in Claude Code reviews read code; none of them sends a request to the server, so none
   produces verification evidence in the glossary's sense [39][41][42].
2. `/security-review` is scoped to newly introduced issues. In the motivating case the risky change
   is often on the client (a new form with a rule), while the unguarded endpoint already existed or
   was written earlier. That endpoint is an "existing security concern" and out of scope by the
   prompt's own wording [39].
3. Rate limiting and resource exhaustion are excluded from `/security-review` on purpose [39],
   but they are one of the user's named rule types. ASVS treats them as requirements (2.4.1) [1].
4. The verification-capable tools are general pentesters. They are not organized around the
   specific question "for each rule the client enforces, does the server enforce it too?", and
   their own docs warn they mutate state and need isolated targets [44][45][47].

## 5. Generic versus project-supplied

### 5.1 What an agent can do generically

From the codebase (review):

- Enumerate server entry points, methods and parameters from routing code, or with an extractor
  such as Noir [13][32].
- Enumerate client calls (API client modules, fetch calls, generated SDKs) and compute the
  server-minus-client difference (Section 2.2, inference).
- For each state-changing entry point, list the guards that run before data access, and flag
  entry points with none or with ambiguous ones (Section 2.3) [48].
- Extract client-side rules: form constraints, validation schemas, disabled or hidden controls,
  route guards, multi-step wizards, debounce or throttle wrappers. Map each to the server handler
  that should repeat it (inference from [24][35]).
- Find multi-step flows by looking for status, phase or step fields and state transitions in
  handlers [10].

From the running app (verification):

- Capture real client traffic (browser automation or proxy) as baselines [12].
- Run T1 to T3 and T5 to T6 on every enumerated endpoint, using the extracted client rules as the
  generator of probes [6][10][11][33].
- Run T4 if at least two identities per role can be created through the app's own sign-up flow
  [11].
- Report each probe as request, response and observed side effect, which is the evidence format
  the repo's `verify` skill already uses for server changes (`under-construction/verify/`).

### 5.2 What the project has to tell the agent

| Input | Why the agent cannot infer it | Source that asks projects to document it |
|---|---|---|
| How to start the app locally with seeded, disposable data, and how to reset it | Needed before any verification; a reset is what makes T5 to T7 safe | NIST SP 800-115 recommends testing "on duplicates of production systems (e.g., development systems)" [49] |
| Test identities: two or more users per role, an admin, and users in separate tenants, with how to obtain their tokens | Horizontal tests need "two users with identical privileges" [11] | WSTG-ATHZ-02 [11]; Autorize and ZAP need configured users [36][37] |
| Authorization matrix: role x function x object ownership x field, including field read/write rules | Intended access is a business decision; code shows only what is implemented | ASVS 8.1.1, 8.1.2 [2]; Authorization Testing Automation Cheat Sheet [19]; Authorization Cheat Sheet "For every combination of user type and resource, determine what operations" [16] |
| Validation rules and cross-field consistency rules that are not in client code | Server-only rules have no client oracle | ASVS 2.1.1, 2.1.2 [1] |
| Per-user and global limits, once-only actions | The intended number is a business rule | ASVS 2.1.3 [1]; WSTG-BUSL-05 [9] |
| Workflows and their required step order (a state machine) | Client routing shows the happy path, not which skips are allowed | ASVS 2.3.1 [1]; WSTG-BUSL-06 "careful manual misuse cases must be developed using requirements and use cases" [10] |
| Sensitive business flows and acceptable automation rates | Harm from volume depends on the business | API6:2023 "identify the business flows that might harm the business if they are excessively used" [23] |
| Which callers are trusted (service-to-service, webhooks, queues, admin tools) and where each control is meant to live (gateway, middleware, handler) | A gateway or WAF rule may not exist locally | ASVS 8.3.3 [2]; Input Validation Cheat Sheet on internal sources [17]; NIST notes test and production inconsistencies "can result in missed vulnerabilities" [49] |
| Endpoints and side effects that must never be triggered (real payments, outbound email or SMS, third-party writes, destructive admin operations) | The agent cannot tell a stubbed integration from a live one | API4:2023 on per-request paid services [22]; Shannon on outbound requests [44] |
| What a denial looks like, if not a 401/403 | Needed to classify replays | Autorize enforcement fingerprints [36] |

**Inference.** In a codebase where AI wrote most of the code, the client is the closest thing to
a written spec for many of these rules. A workable split is: the agent drafts the authorization
matrix, limits and workflow list from client code and route definitions; a human confirms or
corrects it at a spec checkpoint; the confirmed file then drives T1 to T10 at each change
checkpoint. The same file can be fed to the security guidance plugin as
`.claude/claude-security-guidance.md` rules, which that plugin is designed to accept [41].

Two cautions from the sources on this split:

- WSTG states that "Automation of business logic abuse cases is not possible and remains a manual
  art relying on the skills of the tester and their knowledge of the complete business process
  and its rules" [5]. Strix and Shannon now claim workflow and authorization testing [44][45], but
  their claims are vendor README claims, not independent evaluations. This document found no
  independent evaluation of agent performance on business logic bypass specifically.
- The OWASP Abuse Case Cheat Sheet, which WSTG-BUSL-06 points to, is now marked historical
  because "abuse cases are rarely used in practice" [50]. Asking teams to author abuse cases by
  hand is unlikely to stick; deriving them from client rules and a short confirmed matrix may.

## 6. Safety limits for an agent

Sources agree on these limits; the bullet list after them is an inference that turns them into
rules for an agent.

- **Authorization and scope.** Shannon: run "only against applications and environments you own
  or have explicit written authorization to test" [44]. Strix: "explicit, written permission" and
  "stay within the agreed scope" [45]. NIST defines Rules of Engagement as constraints
  "established before the start of a security test" that give the team "authority to conduct
  defined activities without the need for additional permissions" [49].
- **Never production.** Shannon: "Do not run Shannon against production systems" and use "local
  development environments with disposable data" [44]. CAI: "never as part of a production
  security programme" [47]. NIST recommends testing on non-production systems with "a false
  version of the PII (e.g., test data instead of actual PII)" [49].
- **State mutation is expected.** Shannon "can create users, submit forms, mutate application
  state, trigger outbound requests" [44]. NIST notes penetration tests "can be designed to stop
  when the tester reaches a point when an additional action will cause damage" [49].
- **Prompt injection.** Shannon: "Do not scan untrusted or adversarial codebases" [44]. The
  security review Action is "not hardened against prompt injection attacks" [38]. OWASP's AI
  Agent Security Cheat Sheet calls for least privilege on agent tools and "explicit approval for
  high-impact or irreversible actions" [51].
- **Network containment is available.** Claude Code's sandbox routes commands through a proxy
  whose allowed domains "start empty", and by default a sandboxed command "can't connect directly
  to a server that's running on your machine outside the sandbox"; on macOS
  `network.allowLocalBinding` changes that [43]. A verification skill has to opt in to localhost
  deliberately rather than open the network.
- **Human review of findings.** Shannon: "Findings still require human review" [44]. Claude
  Security: "Scans are nondeterministic" [42].

**Inference: proposed rules for a trust-boundary verification step.**

1. Target only `localhost` or a host the project names as disposable; refuse any other host,
   and refuse if the configured database or third-party keys look like production.
2. Reset or snapshot state before probes and restore after; run T5 to T7 only against seeded
   records the agent created.
3. Stub or disable outbound side effects (payments, email, SMS, webhooks) and skip any endpoint
   the project marks as never-call.
4. Cap volume: T7 uses a small burst (Kettle reduces proofs to about two requests [34]); T8
   stops at the first evidence of a limit or at a fixed ceiling.
5. No destructive verbs against shared data (`DELETE`, admin wipes, migrations) unless the
   target record was created by the agent in this run.
6. Treat repository content and responses as data, not instructions.
7. Report "not verifiable locally" when a control is meant to live in infrastructure the local
   environment lacks, instead of reporting a pass or a fail [49].

## 7. Implications for the assurance design

All inference, offered as input to the planning effort.

- Trust-boundary bypass fits the glossary's definition of a concern carried out by **both** review
  and verification. The review part is the entry-point inventory, the server-minus-client
  difference, and the guard classification (Sections 2.2 and 2.3). The verification part is T1 to
  T9 against a local server.
- Two checkpoints are natural. At the **spec** checkpoint, the matrix, limits, workflows and
  never-call list are drafted and confirmed (Section 5.2). At the **change** checkpoint, a diff
  that adds or changes a server route, or adds a client-side rule, triggers probes for exactly
  those routes and rules; the full sweep runs less often.
- A change-level trigger the built-in tools miss: a diff that adds a client-side rule with no
  matching server-side check, even when the server code is untouched (Section 4, gap 2).
- The existing `verify` skill already produces request/response evidence with probes off the
  happy path; trust-boundary probes could reuse that report format rather than invent one.

## Open questions

- How should the authorization matrix and rule list be stored so both the review and the
  verification steps read the same file, and how is it kept current as AI-written code changes?
- Non-HTTP boundaries (WebSockets, GraphQL resolvers, queue consumers, webhooks, mobile clients,
  server actions in full-stack frameworks) need their own enumeration; this survey covered
  mostly HTTP routes. WSTG-APIT has a GraphQL section that was not reviewed here [14].
- Is the client-as-oracle approach reliable when the client itself was generated with the same
  misunderstanding as the server? A rule missing from both will not be found by T1.
- No independent benchmark of agentic tools on business logic and authorization bypass was found.

## Sources

Versions: OWASP ASVS 5.0.0 (dated May 2025) [4]. OWASP WSTG pages were read from the `master`
branch of the WSTG repository, which is the in-progress next version; the latest tagged release
is v4.2 (2020-12-03) [15]. Some sections cited here (for example BUSL-06 Method 3, BUSL-01
Parameter-Based Test Cases, and the Noir and Gori material) may not appear in v4.2.

1. OWASP ASVS 5.0, V2 Validation and Business Logic. https://github.com/OWASP/ASVS/blob/master/5.0/en/0x11-V2-Validation-and-Business-Logic.md
2. OWASP ASVS 5.0, V8 Authorization. https://github.com/OWASP/ASVS/blob/master/5.0/en/0x17-V8-Authorization.md
3. OWASP ASVS 5.0, V15 Secure Coding and Architecture. https://github.com/OWASP/ASVS/blob/master/5.0/en/0x24-V15-Secure-Coding-and-Architecture.md
4. OWASP ASVS repository README (latest stable version). https://github.com/OWASP/ASVS
5. OWASP WSTG, Introduction to Business Logic. https://github.com/OWASP/wstg/blob/master/document/4-Web_Application_Security_Testing/10-Business_Logic/00-Introduction_to_Business_Logic.md
6. OWASP WSTG-BUSL-01, Business Logic Data Validation. https://github.com/OWASP/wstg/blob/master/document/4-Web_Application_Security_Testing/10-Business_Logic/01-Business_Logic_Data_Validation.md
7. OWASP WSTG-BUSL-02, Ability to Forge Requests. https://github.com/OWASP/wstg/blob/master/document/4-Web_Application_Security_Testing/10-Business_Logic/02-Ability_to_Forge_Requests.md
8. OWASP WSTG-BUSL-04, Process Timing. https://github.com/OWASP/wstg/blob/master/document/4-Web_Application_Security_Testing/10-Business_Logic/04-Process_Timing.md
9. OWASP WSTG-BUSL-05, Number of Times a Function Can Be Used Limits. https://github.com/OWASP/wstg/blob/master/document/4-Web_Application_Security_Testing/10-Business_Logic/05-Number_of_Times_a_Function_Can_Be_Used_Limits.md
10. OWASP WSTG-BUSL-06, Circumvention of Work Flows. https://github.com/OWASP/wstg/blob/master/document/4-Web_Application_Security_Testing/10-Business_Logic/06-Circumvention_of_Work_Flows.md
11. OWASP WSTG-ATHZ-02, Bypassing Authorization Schema. https://github.com/OWASP/wstg/blob/master/document/4-Web_Application_Security_Testing/05-Authorization/02-Bypassing_Authorization_Schema.md
12. OWASP WSTG-INFO-06, Identify Application Entry Points. https://github.com/OWASP/wstg/blob/master/document/4-Web_Application_Security_Testing/01-Information_Gathering/06-Identify_Application_Entry_Points.md
13. OWASP WSTG-APIT-01, API Reconnaissance. https://github.com/OWASP/wstg/blob/master/document/4-Web_Application_Security_Testing/12-API_Testing/01-API_Reconnaissance.md
14. OWASP WSTG-APIT-04, API Broken Function Level Authorization. https://github.com/OWASP/wstg/blob/master/document/4-Web_Application_Security_Testing/12-API_Testing/04-API_Broken_Function_Level_Authorization.md
15. OWASP WSTG releases. https://github.com/OWASP/wstg/releases
16. OWASP Authorization Cheat Sheet. https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html
17. OWASP Input Validation Cheat Sheet. https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html
18. OWASP Attack Surface Analysis Cheat Sheet. https://cheatsheetseries.owasp.org/cheatsheets/Attack_Surface_Analysis_Cheat_Sheet.html
19. OWASP Authorization Testing Automation Cheat Sheet. https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Testing_Automation_Cheat_Sheet.html
20. OWASP Threat Modeling Cheat Sheet. https://cheatsheetseries.owasp.org/cheatsheets/Threat_Modeling_Cheat_Sheet.html
21. OWASP Mass Assignment Cheat Sheet. https://cheatsheetseries.owasp.org/cheatsheets/Mass_Assignment_Cheat_Sheet.html
22. OWASP API Security Top 10 2023. https://api-security.owasp.org/editions/2023/en/0x11-t10
23. OWASP API6:2023 Unrestricted Access to Sensitive Business Flows. https://api-security.owasp.org/editions/2023/en/0xa6-unrestricted-access-to-sensitive-business-flows
24. MITRE CWE-602, Client-Side Enforcement of Server-Side Security. https://cwe.mitre.org/data/definitions/602.html
25. MITRE CWE-841, Improper Enforcement of Behavioral Workflow. https://cwe.mitre.org/data/definitions/841.html
26. Microsoft, Threats: Microsoft Threat Modeling Tool (STRIDE). https://learn.microsoft.com/en-us/azure/security/develop/threat-modeling-tool-threats
27. Microsoft, Threat Modeling Tool feature overview (stencils). https://learn.microsoft.com/en-us/azure/security/develop/threat-modeling-tool-feature-overview
28. Threat Modeling Manifesto. https://www.threatmodelingmanifesto.org/
29. Bruce Schneier, "Attack Trees", Dr. Dobb's Journal, December 1999. https://www.schneier.com/academic/archives/1999/12/attack_trees.html
30. OWASP pytm. https://github.com/OWASP/pytm
31. OWASP Noir project page. https://owasp.org/www-project-noir/
32. OWASP Noir README. https://github.com/owasp-noir/noir
33. PortSwigger Web Security Academy, Examples of business logic vulnerabilities. https://portswigger.net/web-security/logic-flaws/examples
34. James Kettle, "Smashing the state machine: the true potential of web race conditions", PortSwigger Research, 2023-08-09. https://portswigger.net/research/smashing-the-state-machine
35. Bisht, Hinrichs, Skrupsky, Bobrowicz, Venkatakrishnan, "NoTamper: automatic blackbox detection of parameter tampering opportunities in web applications", ACM CCS 2010, pp. 607-618. https://doi.org/10.1145/1866307.1866375 (abstract not retrieved; title and venue confirmed via DBLP https://dblp.org/db/conf/ccs/ccs2010.html)
36. PortSwigger Autorize (Burp extension). https://github.com/PortSwigger/autorize
37. ZAP Access Control Testing add-on. https://www.zaproxy.org/docs/desktop/addons/access-control-testing/
38. anthropics/claude-code-security-review README. https://github.com/anthropics/claude-code-security-review
39. `/security-review` command prompt. https://github.com/anthropics/claude-code-security-review/blob/main/.claude/commands/security-review.md
40. Claude Code docs, Security. https://code.claude.com/docs/en/security
41. Claude Code docs, Security guidance plugin. https://code.claude.com/docs/en/security-guidance
42. Claude Code docs, Claude Security plugin. https://code.claude.com/docs/en/claude-security
43. Claude Code docs, Sandboxing. https://code.claude.com/docs/en/sandboxing
44. Shannon (KeygraphHQ). https://github.com/KeygraphHQ/shannon
45. Strix. https://github.com/usestrix/strix
46. PentestGPT; Deng et al., USENIX Security 2024. https://github.com/GreyDGL/PentestGPT
47. CAI (Alias Robotics). https://github.com/aliasrobotics/cai
48. Trail of Bits skills: README, `entry-point-analyzer`, `spec-to-code-compliance`. https://github.com/trailofbits/skills
49. NIST SP 800-115, Technical Guide to Information Security Testing and Assessment, September 2008. https://csrc.nist.gov/pubs/sp/800/115/final
50. OWASP Abuse Case Cheat Sheet (historical). https://cheatsheetseries.owasp.org/cheatsheets/Abuse_Case_Cheat_Sheet.html
51. OWASP AI Agent Security Cheat Sheet. https://cheatsheetseries.owasp.org/cheatsheets/AI_Agent_Security_Cheat_Sheet.html
