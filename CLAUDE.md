# CLAUDE.md — LLM Agent Harness From Scratch

> Context file so we keep continuity across sessions. Update Status and the
> Decision Log whenever something changes. Read this first at the start of every
> session. Full design-space rationale (branches, alternatives, dated-instinct
> ledger) lives in [llm-harness-plan_1.md](llm-harness-plan_1.md) — this file is
> the live/compressed version of it, kept in sync as decisions firm up.
>
> **Legacy note:** this project pivoted away from the earlier GSM8K /
> inference-time-compute-scaling plan. That plan is preserved as-is in
> [CLAUDE_legacy_gsm8k_plan.md](CLAUDE_legacy_gsm8k_plan.md) for later comparison —
> not current, do not follow it.

## What this project is

A portfolio project: **build an LLM agent harness from scratch** (control loop,
tool layer, context management, sandboxed execution, eval runner), then benchmark
it against a bare (no-harness) model and 1–2 existing open-source harnesses — same
model(s), same tasks, real numbers, honest writeup.

**Core thesis this project demonstrates:** harness choice moves benchmark scores
as much as or more than model choice (2026 research shows swings up to 23 points
between harnesses on the *same* model). "My harness vs. bare model vs. OSS
harness(es), same model, same tasks" is a live, legitimate experimental axis, not
a toy comparison.

**Not novel, and we don't claim novelty.** Value = rigor + genuine understanding:
a hand-written agent core, clean ablations, honest error bars, a documented
failure taxonomy, and a rejected-alternatives section that shows the design space
was actually considered.

## Audience & success

- Reviewed by senior engineers/interviewers as a resume project. Target roles:
  GenAI / LLM / agent-infra engineer.
- **Success =** a working hand-built harness; a results table (bare model vs. our
  harness vs. mini-swe-agent vs. optionally smolagents) with confidence intervals
  on a fixed-model, fixed-task-suite grid; a failure taxonomy; 1-2 measured
  ablations (context policy, native-vs-text tool protocol, etc.).
- **Explicit non-goal:** beating frontier harnesses/models. The comparison is
  harness-vs-harness at a fixed (cheap/mid-tier) model, not vs. frontier.

## The one hard rule (non-negotiable)

**The agent core is hand-written; AI assists everywhere else.** Core = control
loop, context manager, tool dispatch (~300–500 lines total). Understanding comes
from the build-debug loop on exactly this code — watching a loop run forever
because a termination condition never fires, watching context blow the window,
watching the model hallucinate a tool. If a coding assistant writes this part,
skip it and the project's actual purpose is defeated. AI/agents ARE allowed for:
Dockerfiles, eval-runner plumbing, plotting, README polish, baseline glue code,
rubber-ducking when stuck.

**Recommended first step before building:** read `mini-swe-agent`'s ~100 lines
once, close the file, then build your own without looking. Cheap way to get the
mental model without skipping the part that earns it.

## Key decisions (Decision Log)

- **D1: Coding/terminal agent, not a research/web agent.** Objective grading (run
  tests / check exit codes, no LLM judge needed), canonical baselines already
  exist (mini-swe-agent), reproducible (Docker vs. live web), and cheap models are
  far more competent at "run bash, edit file, run tests" than long-horizon web
  research. Research-agent (GAIA) path fully mapped as rejected alternative in
  plan §8.2 — revisit only if this path stalls badly.
- **D2: Client layer = LiteLLM (or OpenAI SDK + OpenRouter)** for the build proper,
  after a raw-HTTP exercise (no SDK) to demystify the wire format first. Enables
  swapping models with one string change, which the benchmark grid needs.
- **D3: Control loop = plain ReAct, single agent, one action per turn.** Current
  2026 evidence: minimal harnesses match/beat feature-heavy ones with capable
  models. Plan-then-execute and reflection/self-critique are cheap ablations to
  bolt on later, not defaults. Multi-agent orchestration explicitly rejected
  (complexity without capability at this scale) — note as considered-and-rejected
  in the README.
- **D4: Tool set v1 = `bash` + `submit` only.** Deliberately tiny and defensible
  (mini-swe-agent scores >74% SWE-bench Verified bash-only). Structured file tools
  (`read_file`, `str_replace_edit`, `grep` — the Claude Code/SWE-agent ACI school)
  are the v2 upgrade, done as a measured ablation, not a v1 requirement.
- **D5: Support both native tool-calling and text-protocol (fenced-block) actions
  behind one interface (~30 lines extra).** Gives a real ablation (native vs. text
  protocol, same model, same tasks) with little existing published data for cheap
  models specifically.
- **D6: Sandbox = Docker container per episode**, `bash` via `docker exec`
  (or prepend `cd $WORKDIR &&` per call and accept statelessness rather than
  building a persistent shell). Network off by default. Resource caps
  (`--memory`, `--cpus`).
- **D7: Comparison systems** — Baseline A = bare model, single call, no loop/tools
  (mandatory, defines the headline gap). Baseline B = mini-swe-agent, pinned
  commit (mandatory, field-standard reference point). Baseline C (recommended) =
  smolagents, for a second paradigm (code-as-action vs. tool-calling loop).
  Model held fixed across all systems (or run the full grid over 2 models).
- **D8: Primary task suite = fixed subset (30–50 instances) of SWE-bench
  Lite/Verified**, official per-task Docker images + official grading scripts only
  (never reimplement grading). Optional secondary: 10–15 hand-written planted-bug
  tasks (contamination-immune, shows benchmark-design understanding) — additive,
  not a replacement.
- **D9: Statistics are mandatory, not decoration.** k≥3 runs per config (temp 0 is
  not deterministic across providers). Report pass@1 (mean) and pass^k (all-k
  reliability). Wilson 95% CI on every success rate; refuse "A beats B" claims
  under overlapping intervals. Report cost/tokens/steps-to-solve per solved task,
  not just success rate. Full failure taxonomy from traces (wrong edit / never
  reproduced / step-limit loop / context overflow / malformed action / crash).
- **D10: Context management order of implementation** (each measured as an
  ablation): (1) observation truncation (head+tail, mandatory) → (2) observation
  aging/masking (keep last K full, stub older ones) → (3) compaction/summarization
  (branch, adds a failure mode) → (4) external memory/retrieval (out of scope,
  next project).
- **D11: Traces are the most load-bearing artifact.** One JSONL file per episode:
  every request/response/action/observation/token-count/cost/wall-time/
  termination-reason. Eval runner, failure analysis, and report all read this
  format — get it right early, don't redesign it mid-project.

## Hard constraints / logistics

- **Timeline:** ~6–8 weeks part-time (per plan §2 calendar), alongside other
  commitments. Not the ASAP 1-week cadence of the old GSM8K plan.
- **Budget:** rough order tens of dollars, not hundreds — pilot 5 tasks across all
  systems first and extrapolate before running the full grid (full grid ≈50 tasks
  × 4 systems × 3 seeds ≈ 600 episodes; ⏱ re-check current cheap-tier token
  pricing before committing to the full run).
- **⏱ Re-check before relying on, mid-build (per plan §0/§12):** SWE-bench
  tooling/current docs (plan retired Verified for frontier use in 2026 — fine for
  this cheap-model harness study, just frame it honestly); mini-swe-agent pinned
  commit/version; MCP spec version if adding an MCP adapter stretch goal.

## Backward-chained spine (build order)

N1 fundamentals (raw HTTP, tokens, tool-calling wire format) → N2 LLM client →
N3 control loop → N4 tool layer → N5 context mgmt/limits/observability → N6
Docker sandbox → N7 eval runner → N8 statistically defensible eval (CIs, k runs) →
N9 end state (repo + report). Full node-by-node writeup with branch tables:
[llm-harness-plan_1.md](llm-harness-plan_1.md) §2–9.

## Milestones & status

- [ ] **M1:** raw-HTTP 3-turn tool-call exercise; loop + fake tool; bash-in-tempdir
      "write 10 primes" works.
- [ ] **M2:** Docker sandbox; 3 hand-made toy bugs solved end-to-end; JSONL traces
      + limits (steps/cost/timeout) in place.
- [ ] **M3:** SWE-bench official images running locally; harness completes 5 real
      instances (any score); official grading scripts.
- [ ] **M4:** eval runner resumable + parallel; bare-model baseline scripted;
      5-task pilot across all systems; extrapolate budget from it.
- [ ] **M5:** full grid (~50 tasks × systems × 3 seeds); stats + CIs + failure
      taxonomy.
- [ ] **M6:** 1–2 ablations run; README/report written; publish.

**Current status:** Plan adopted, decisions logged (D1–D11). Old GSM8K/
distillation project retired — see legacy file. Next: M1 (raw-HTTP exercise +
control loop + fake tool), and read mini-swe-agent's source once before writing
the hand-rolled loop.

## End-state repo shape

```
your-harness/
├── README.md            # results table up top, then architecture, then
│                        # design decisions incl. rejected branches
├── harness/             # ~300-500 hand-written lines
│   ├── loop.py          # control loop
│   ├── llm.py           # client
│   ├── tools.py         # bash/submit + dispatcher
│   ├── context.py       # truncation/aging policy
│   └── sandbox.py       # docker exec wrapper
├── eval/                # runner, grading glue, stats, plots
├── baselines/           # pinned configs/commits: mini-swe-agent, smolagents,
│                        # bare-model script
├── traces/              # sample JSONL traces + tiny HTML viewer
└── report.md            # methods, results w/ CIs, failure taxonomy,
                         # ablations, honest limitations
```

Reviewer priority order: (1) results table w/ CIs + fixed-model methodology note,
(2) failure-taxonomy table, (3) ablations, (4) rejected-alternatives section,
(5) contamination/saturation honesty.

## Conventions

- **Reproducibility:** fix seeds, pin dependencies and baseline commits, log every
  run config, one-command reproduce script. Save raw traces — never re-generate
  to re-score.
- **Learning rule:** the agent core is hand-written by the user; coding agents
  read/comment but do not write loop.py/llm.py/tools.py/context.py. Everything
  peripheral (Docker, eval plumbing, plots, README, baseline wiring) is fair game
  for AI assistance.
- **Prior art to know:** ReAct (Yao 2022), mini-swe-agent, smolagents/CodeAct,
  SWE-bench/SWE-agent, Terminal-Bench, MCP, tau-bench.

## Background calibration (user)

- Python: knows syntax, uses coding agents, wants to learn as we go.
- New ground vs. the old GSM8K project: Docker sandboxing, tool-calling wire
  format, SWE-bench grading mechanics. Carried over: seriousness about CIs and
  compute/cost accounting.
