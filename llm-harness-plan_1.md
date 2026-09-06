# Building an LLM Harness From Scratch — Standalone Planning Reference

**Written:** August 2026. Grounded in web research current as of that date. Anything in this space older than ~6 months should be re-verified before you rely on it; re-verification points are flagged inline as **⏱ RE-CHECK**.

**How this document is organized.** Every major section is written to stand alone — terms are re-defined where they're used, so you can lift a section into a fresh conversation with a cheaper model without dragging the rest along. Two labels appear throughout:

- **[SPINE]** — the backward-chained critical path. This is the ~20% you actually build. Read the spine sections in order and you have the whole project.
- **[BRANCH]** — the design-space map around each spine node. Realistic alternatives with genuine trade-offs. You won't build these, but knowing they exist (and why you didn't pick them) is most of the understanding you said you're after — and it's what makes the README/writeup portfolio-grade.

---

## 0. [SPINE] The Honest Read: Is "Plan Once With a Strong Model, Build With Cheap Tools" a Good Strategy?

You asked for this straight, so: **it's about 70% right, and the 30% that's wrong is predictable and fixable.**

**What's right about it.** The expensive part of a strong model's value here is *map-making* — knowing the whole design space, what's current, what's a dead end, what the benchmark landscape looks like. That's exactly what a one-time planning session buys, and it's exactly what cheap models are worst at (they'll confidently describe the 2024 landscape). The build itself — writing a control loop, wiring an API client, debugging Docker — is well within cheap-model territory, because at build time *you* have ground truth: the code either works or it doesn't. So the division of labor is sound.

**Failure mode #1: the plan goes stale, and you treat it as a spec.** Agent tooling and benchmarks move on a ~3–6 month cycle. Concrete example from this research pass: OpenAI published a note in 2026 titled "Why SWE-bench Verified no longer measures frontier coding capabilities" — a benchmark that was *the* standard when most training data was written is now considered saturated at the frontier. If you follow this document as gospel in six months, some node will be quietly wrong. **Fix:** treat this as a map, not a spec. The **⏱ RE-CHECK** flags mark the ~4 places where a 10-minute web search mid-build is worth doing. Everything else (control loops, context windows, statistics) is stable knowledge.

**Failure mode #2 — the one that actually threatens your goal: the cheap AI writes the code and you supervise.** Your stated objective is *understanding*, and understanding of systems like this comes almost entirely from the build-debug loop — watching the agent loop forever because your termination condition never fires, watching context blow past the window because you appended raw tool output, watching the model hallucinate a tool that doesn't exist. If you paste a spine section into a coding assistant and accept a working implementation, you skip precisely the part that produces the understanding. **Fix:** a hard personal rule — *the agent core (loop, context manager, tool dispatch — maybe 300–500 lines) is hand-written; cheap AI is allowed for everything peripheral* (Dockerfiles, eval-runner plumbing, plotting, README polish, and as a rubber duck when you're stuck). That's also the honest version of the portfolio claim "I built this."

**One genuinely better alternative to consider (cost: $0).** The single highest-density learning artifact in this space is `mini-swe-agent` — ~100 lines of Python from the SWE-bench authors that scores >74% on SWE-bench Verified with strong models. It *is* the compressed answer to "how do these systems work." The better sequence than "plan → build": **plan → read those 100 lines once → close the file → build your own without looking.** You get the mental model cheaply, and the build still forces you to earn it. (It's also your baseline harness later, so you'll read it eventually anyway — see §7.)

**Verdict:** keep your strategy, with the two fixes above. The plan below is written assuming you take them.

---

## 1. [SPINE] What "Harness" Should Mean Here — and Which Kind of Agent to Build

**Definition (current usage, 2026).** An **LLM harness** (also called *scaffold* or *agent scaffold*) is everything wrapped around a base language model that turns single-turn text prediction into multi-step task completion: the system prompt, the tool/action interface, the control loop that alternates model calls with tool executions, the context-management policy (what history the model sees each turn), the execution environment (usually a sandbox), and the termination/limit logic. The model is the engine; the harness is the car. This is exactly what you described, so **no, "harness" doesn't need to mean anything narrower** — your instinct matches how the research literature uses the word.

One fact from current research that should shape your whole project: **harness choice moves benchmark scores as much as or more than model choice.** A 2026 spatial-biology benchmark found a 23-point swing between harnesses on the *same model* — larger than the gap between Opus and Sonnet under one harness. Terminal-Bench's own authors describe it as "heavily harness-dependent." This is great news for you: it means "my harness vs. bare model vs. existing harness, same model, same tasks" is not a toy comparison — it's the live experimental axis in the field right now, and a paper published in mid-2026 (Claw-SWE-Bench) does essentially your project at research scale. Your portfolio story writes itself.

**Do you need to lock in the agent type before backward-chaining?** Mostly no. Roughly 80% of the spine — LLM client, control loop, tool dispatch, context management, tracing, statistics — is identical whether the agent codes, researches, or books flights. The choice only bites at two nodes: *which tools you give it* (§6) and *which benchmark grades it* (§8). So the plan below flexes, but I'll make the call I'd make and you can override once you see the shape:

**Recommendation: build a coding/terminal agent.** Reasons, in order of weight:

1. **Grading is objective and free.** Coding benchmarks (SWE-bench family, Terminal-Bench) grade by running the repo's unit tests or checking exit codes — ground truth, no LLM judge, no ambiguity. Research/Q&A benchmarks (GAIA-style) need exact-match answer normalization and sometimes an LLM judge for ~15% of tasks, which adds cost, noise, and a methodological asterisk to every number you report.
2. **Your baselines already exist and were designed for exactly this.** `mini-swe-agent` exists explicitly "as a baseline system" for harness comparisons. There is no equivalently canonical minimal baseline for research agents.
3. **Reproducibility.** A coding task in a Docker container is deterministic-ish. A research agent hits the live web — pages change, results reorder, your benchmark numbers rot within weeks and nobody can reproduce them.
4. **Cheap-model compatibility.** Small/cheap models are markedly better at "run bash, edit file, run tests" than at long-horizon web research, so your numbers will show real signal instead of a floor of zeros.

The research-agent alternative is mapped fully in §8-BRANCH so you can still pick it deliberately.

---

## 2. [SPINE] The Backward Chain — Project Spine at a Glance

Read bottom-up for "what depends on what"; build top-down (N1 → N9). Each node gets its own section below with its branch map.

```
N9  END STATE: public repo + benchmark report
    "My harness vs. bare model vs. 1–2 OSS harnesses,
     same model(s), same tasks, real numbers + honest writeup"
      ▲ requires
N8  A statistically defensible eval: task suite, ≥3 runs/config,
    confidence intervals, cost/steps/tokens logged per run
      ▲ requires
N7  An eval runner: script that executes {harness × task × seed},
    grades outcomes against ground truth, dumps structured results
      ▲ requires
N6  A sandboxed execution environment (Docker per task) — both for
    safety (agent runs arbitrary shell commands) and for grading
      ▲ requires
N5  Harness "production" features: context-window management,
    error handling, step/cost limits, full trace logging
      ▲ requires
N4  A tool layer: the actions the model can take (bash, file edit,
    ...), their schemas, and the dispatcher that executes them
      ▲ requires
N3  The control loop: call model → parse intended action →
    execute → append observation → repeat until done/limits
      ▲ requires
N2  An LLM client: one function that sends a message list to a
    model API and returns text + structured tool calls
      ▲ requires
N1  FUNDAMENTALS: what an LLM API call actually is — messages,
    tokens, context window, statelessness, how "tool calling"
    works on the wire
```

Suggested calendar (part-time, alongside your internship): N1–N3 one weekend, N4–N5 one to two weeks, N6–N7 one to two weeks, N8 one week of runs + analysis, N9 one week of writing. **6–8 weeks total.** Budget: see §8 (rough order: tens of dollars, not hundreds, if you use cheap models and small task subsets).

---

## 3. [SPINE] N1 — Fundamentals: What You're Actually Calling

*Standalone context: this section assumes nothing.*

An LLM API (OpenAI, Anthropic, Google, or any OpenAI-compatible endpoint like OpenRouter/Ollama) is a **stateless HTTP endpoint**. Every call sends the *entire conversation so far* as a list of messages and gets back one new message. The model remembers nothing between calls; all "memory" is you re-sending history. This one fact generates most of harness design: context management exists because the history you re-send grows every step and the model has a hard cap (**context window**, measured in **tokens** — subword chunks, ~0.75 words each; typical windows in 2026 are 200k–1M+ tokens, but cost scales with tokens sent, so "fits" ≠ "affordable").

A request, schematically:

```
POST /v1/messages   (shape varies slightly by provider)
{
  "model": "some-model-id",
  "system": "You are a software engineering agent...",
  "messages": [
    {"role": "user",      "content": "Fix this bug: ..."},
    {"role": "assistant", "content": "I'll look at the file...",
                           "tool_calls": [{"name": "bash",
                                           "args": {"cmd": "cat main.py"}}]},
    {"role": "tool",      "content": "<stdout of that command>"}
  ],
  "tools": [ {"name": "bash",
              "description": "Run a shell command",
              "input_schema": {"cmd": "string"}} ],
  "temperature": 0.0,
  "max_tokens": 4096
}
```

**What "tool calling" (a.k.a. function calling) actually is:** you describe available functions as JSON schemas in the request; the model, instead of (or alongside) prose, emits a structured JSON blob saying "call `bash` with `{cmd: ...}`". **The API does not run anything.** Your code reads that blob, executes whatever it means, and sends the result back as a new message. The model was fine-tuned to emit this format reliably — that's the entire magic. Two implications worth internalizing early: (a) an "agent" is just this request in a while-loop, and (b) nothing forces you to use the native tool-calling format — you can equally instruct the model to write actions in plain text (e.g. a fenced ```bash block) and parse it yourself, which is exactly what `mini-swe-agent` does. §6-BRANCH covers that trade-off.

Other knobs you'll touch: `temperature` (0 = near-deterministic — *near*, not fully; providers don't guarantee bitwise determinism, which is why §9 makes you run everything multiple times), `max_tokens` (cap on the *response* length only), and per-provider **prompt caching** (re-sent unchanged prefixes are billed at ~10% — matters a lot for agents, since each step re-sends everything).

**Exercise that constitutes "done" for N1:** with raw `requests`/`curl` (no SDK), hold a 3-turn conversation with a model where turn 2 is a tool call you execute by hand. Under an hour, and it demystifies the whole stack.

### 3-BRANCH: How to talk to the model — the client-layer design space

| Option | What it is | Trade-off |
|---|---|---|
| **Raw HTTP, one provider** | `requests.post` to Anthropic/OpenAI | Maximum understanding, zero deps. Locks you to one provider's format. Fine for N1; limiting by N8 (you'll want to swap models). |
| **Official SDK, one provider** | `anthropic` / `openai` pip packages | Ergonomic, handles retries/streaming. Still single-format. |
| **LiteLLM** (or the OpenAI SDK pointed at OpenRouter) | Translation layer: one call signature, 100+ providers | The pragmatic 2026 default for a project like yours — model-swapping is one string change, which your benchmark (same harness × multiple models) directly needs. Cost: one dependency, occasional leaky abstraction around provider-specific features (caching, thinking modes). `mini-swe-agent` uses LiteLLM. |
| **Local models** (Ollama, vLLM) | Self-hosted open weights | Free tokens, full reproducibility. But small local models are noticeably worse at multi-step tool use; on a T4-Colab-class budget you'd spend the project fighting the model. Reasonable as a *third* model column in your final table, not the primary. |
| **Provider "agent SDKs"** (OpenAI Agents SDK, Claude Agent SDK) | Pre-built loop + tools + tracing | Explicitly out: they *are* the harness. Using one defeats the project. Worth reading their docs after you build, as a "what did the pros do differently" check. |

**Spine pick:** raw HTTP for the N1 exercise, then LiteLLM (or OpenAI SDK + OpenRouter) for the build.

---

## 4. [SPINE] N3 — The Control Loop (the heart, ~50 lines)

*Standalone context: an LLM API is stateless; each call sends full message history and may return a structured "tool call" the caller must execute. The loop below is what makes it an agent.*

**Definition.** The **control loop** (or *agent loop*) alternates model calls with action executions until a termination condition. The dominant pattern is **ReAct** (Reason + Act, Yao et al. 2022): each step the model produces reasoning plus one action; the environment returns an observation; repeat. In 2026 this is so standard that native tool-calling APIs *are* ReAct with the parsing done for you.

```
function run_agent(task, tools, limits):
    messages = [system_prompt(tools), user(task)]
    for step in 1..limits.max_steps:
        response = llm(messages, tools)           # N2
        messages.append(response)
        if response.declares_done():              # model says finished
            return extract_result(response)
        if not response.has_action():             # model just talked
            messages.append(user("Reply with an action or declare done."))
            continue
        obs = execute(response.action)            # N4/N6: sandboxed
        obs = truncate(obs, max_obs_tokens)       # N5: context mgmt
        messages.append(tool_result(obs))
        if cost_so_far() > limits.max_cost: break
    return failure("limits exhausted", messages)  # keep the trace!
```

The non-obvious design decisions hiding in those lines — each is a real decision, not boilerplate:

1. **Termination.** How does the model "declare done"? Options: a special tool (`submit(answer)` / `finish()`), a magic string in prose, or "stopped calling tools = done." The special-tool approach is the most robust and is the modern default; prose-parsing is fragile; implicit-done causes premature exits with weak models.
2. **The three exhaustion paths** — model declares done, step limit, cost limit — must all return the full message trace, because failed traces are where all your learning (and your report's error-analysis section) comes from.
3. **Malformed actions.** Cheap models *will* emit invalid tool calls. The right move is almost never to crash: feed the parse error back as an observation ("Error: unknown tool 'bassh'. Available: bash, submit.") and let the model self-correct. Cap the consecutive-error count (~3) to avoid loops.
4. **One action per step vs. several.** Allowing parallel tool calls complicates everything downstream; serialize to one action per turn for v1.

**Exercise that constitutes "done" for N3:** loop + a fake `add(a,b)` tool; ask the model to sum three numbers using the tool twice. Then swap in real bash and give it "create a file containing the first 10 primes" in a scratch directory.

### 4-BRANCH: Loop architectures beyond plain ReAct

*(This is the densest part of the design space — most "agent frameworks" are one of these patterns productized.)*

| Pattern | Idea | When it wins / loses |
|---|---|---|
| **Plain ReAct single loop** *(spine pick)* | One model, one loop, tools | Current evidence strongly favors it: 2026 research repeatedly finds minimal harnesses matching or beating feature-heavy ones with capable models (mini-swe-agent outscoring Claude Code and complex harnesses on several suites). Loses only when the model is weak or the task needs structure the model can't hold. |
| **Plan-then-execute** | First call produces an explicit multi-step plan; loop executes steps, optionally re-planning | Helps weak models stay on track; adds latency and rigidity (bad plans get executed faithfully). Cheap to bolt on later as an ablation: it's just a different system prompt + a plan slot in context — actually a great *experiment* for your report. |
| **Reflection / self-critique** (Reflexion-style) | After failure, model critiques its own trace and retries with the critique in context | Measurable gains on some suites; doubles cost. Another cheap ablation. |
| **Multi-agent (orchestrator + workers)** | A router model delegates subtasks to specialist loops (CrewAI/AutoGen territory) | Fashionable; the 2026 consensus (incl. AAIF-adjacent commentary) is that most single-agent products dressed as multi-agent buy complexity without capability. Skip for this project; mention in README as considered-and-rejected with this reasoning — that reads as judgment, not laziness. |
| **Graph/state-machine workflows** (LangGraph paradigm) | Explicit DAG of nodes with typed state, retries, human-approval gates | The production-engineering answer: shines when you need durability, resumability, audit. For a learning harness it hides exactly the loop you're trying to learn. |
| **Code-as-action** (smolagents' signature paradigm, CodeAct lineage) | Model writes a Python snippet each step; snippet *is* the action; tools are just functions in scope | Genuinely different philosophy: composition (loops, conditionals over tool calls) comes free, fewer round-trips. Costs: you must sandbox arbitrary Python (harder than sandboxing bash-in-Docker), and error surfaces are messier. Strong candidate for your *second baseline* so your comparison spans both paradigms (§7). |
| **Tree search / best-of-n over trajectories** | Sample multiple rollouts, pick best by verifier | Research-grade, multiplies cost by n. Know it exists; skip. |

---

## 5. [SPINE] N5 — Context Management, Limits, and Observability

*Standalone context: an agent loop re-sends the entire message history to a stateless LLM API every step; history grows every step; the model has a token cap and you have a dollar cap.*

This node is what separates "demo" from "harness," and it's disproportionately where your benchmark deltas will come from. Three sub-systems:

**(a) Context-window management.** Policies, cheapest first — implement in this order and *measure each as an ablation* (this is a ready-made results table for your report):

1. **Observation truncation** *(spine, mandatory)*: cap every tool output at N tokens (e.g. 2k–4k), keeping head + tail with a `[... 14,213 chars truncated ...]` marker. Head+tail beats head-only because errors live at the end of logs.
2. **Observation aging / masking** *(spine, high value-per-line)*: keep only the last K observations at full length; replace older ones with one-line stubs ("step 4: ran pytest, 3 failed"). The model rarely needs step-3 stdout at step 20. `mini-swe-agent`-class harnesses live on variants of 1+2.
3. **Compaction / summarization** *(branch)*: when context crosses a threshold (say 70% of window or of your cost budget), have the model (or a cheaper model) summarize the trajectory so far into a structured note, then restart the message list as `[system, task, summary, recent steps]`. This is what production CLIs (Claude Code etc.) do. Adds a failure mode: bad summaries silently lose the critical detail.
4. **External memory / retrieval** *(branch)*: write facts to a scratchpad file or vector store, retrieve on demand. Overkill for single-task episodes; the natural next project, not this one.

**(b) Limits & failure handling** *(spine)*: max steps (30–50 for coding tasks), max cost per episode (e.g. $0.50), max wall-clock per tool call (subprocess timeout — the agent *will* run a server that never exits), max consecutive malformed actions, and API-level retry with exponential backoff on 429/5xx (transient rate-limit errors). Every limit-hit is recorded as a distinct failure reason — your report's failure taxonomy depends on this.

**(c) Observability** *(spine)*: log every episode as one JSONL trace — every request, response, action, observation, token counts, cost, wall time, termination reason. Plain JSONL files are entirely sufficient. **Branch:** dedicated LLM-observability platforms (Langfuse — which you already know from work — Phoenix/Arize, LangSmith, W&B Weave) give you trace UIs and cost dashboards for free; nice, but a 40-line HTML trace-viewer script is a better learning exercise and one less dependency. Either way: *the trace format is the most load-bearing schema in the project* — the eval runner (§8), the failure analysis, and your report all read it.

### 5-BRANCH: prompt engineering as a system component

The system prompt is part of the harness and worth versioning like code. Current practice worth encoding: state the loop contract explicitly ("each turn: think briefly, then exactly one tool call; call submit when done"), describe tools with examples, state limits ("you have ~40 steps"), and give a suggested workflow (mini-swe-agent's prompt literally walks through locate → reproduce → edit → re-run — and researchers note this workflow-prompt is itself worth points on SWE-bench-style tasks; keep yours honest and note it in your methods section). Treat prompt variants as ablations with numbers, not vibes.

---

## 6. [SPINE] N4 + N6 — Tools and the Sandbox

*Standalone context: an agent harness lets a model take actions ("tools"); the harness executes them and returns output. A coding agent's actions run arbitrary shell commands, so execution must happen inside a disposable sandbox, not on your machine.*

**Spine tool set — deliberately tiny:**

| Tool | Schema | Notes |
|---|---|---|
| `bash` | `{cmd: string}` | Run in the sandbox with a timeout (~60s), return stdout+stderr+exit code. This alone is Turing-complete for the task: reading, searching, editing (`sed`, heredocs), testing all go through it. |
| `submit` | `{summary: string}` (coding: the diff is read from git) | Explicit termination signal. |

That's it for v1, and it's a defensible *choice*, not a shortcut: mini-swe-agent uses literally only bash ("doesn't even need the tool-calling interface") and scores >74% SWE-bench Verified with strong models. The interesting question — and a headline experiment for your report — is whether *cheap* models do better with richer structured tools. Which brings us to:

**The wire-format decision (genuinely contested):**

- **Native tool calling** *(spine pick)*: send JSON schemas, receive structured calls. Pros: models are fine-tuned for it, parsing is free, transfers to how everything commercial works. Cons: format quality varies across cheap/open models.
- **Text-protocol actions** (mini-swe-agent style): system prompt says "put your command in a ```bash fence"; you regex it out. Pros: works with *any* model including ones with weak tool-calling, dead simple, fully transparent. Cons: hand-rolled parsing, occasional format drift.
- Making your harness support **both behind one interface** is ~30 lines and gives you another real ablation: native vs. text protocol, same model, same tasks. Little published data exists on this for cheap models — a place your numbers could be genuinely novel.

**Sandbox — Docker container per episode** *(spine)*: image with git + python + build tools; workspace mounted or baked in; `docker exec` per bash call (or one long-lived shell via `pexpect` if you need `cd`/env persistence — simpler alternative: prepend `cd $WORKDIR &&` to every command and accept statelessness). Fresh container per task; destroy after grading. Network: off by default, on only if the task needs pip installs — and note that SWE-bench official images pre-install dependencies precisely so network can stay off. Resource caps (`--memory`, `--cpus`) because agents occasionally fork-bomb by accident.

### 6-BRANCH: the wider tool/action design space

| Alternative | Trade-off vs. bash-only |
|---|---|
| **Structured file tools** (`read_file`, `str_replace_edit`, `grep`) — the Claude Code / SWE-agent "ACI" (agent-computer interface) school | Frontier vendors ship these because models are *trained on them*, and precise string-replace edits fail less than heredoc/sed gymnastics for mid-tier models. Costs: more schemas to design, more parsing edge cases (non-unique match strings...). The canonical v2 upgrade; do it as a measured ablation. |
| **Code-as-action** (smolagents): model writes Python, tools are in-scope functions | Elegant composition; needs a Python sandbox (restricted interpreter or the same Docker); different failure texture. Covered as a baseline in §7 instead of a build target. |
| **MCP (Model Context Protocol)** — the open JSON-RPC standard for exposing tools to any model/client; released by Anthropic Nov 2024, donated to the Linux Foundation's Agentic AI Foundation in Dec 2025, and by 2026 the settled cross-vendor tool-integration layer (Anthropic, OpenAI, Google, Microsoft all support it) | Important distinction: MCP is *not* an alternative to function calling — function calling is the model-API mechanism, MCP is the integration layer above it (build a tool server once, any client uses it). For a self-contained benchmark harness it adds indirection with no benefit — your two tools don't need a protocol. **But**: adding a thin "consume an MCP server" adapter as a v3 stretch is high resume-value in 2026, and teaches the standard everyone now hires for. ⏱ RE-CHECK spec version if you do this — it revs several times a year. |
| **Browser/web tools** (search, fetch, click) | The research-agent path; see §8-BRANCH. Reproducibility poison for benchmarks. |
| **Sandbox alternatives** | Plain subprocess + temp dir (fine for week 1, unsafe + un-gradeable for real repos); VM-grade micro-VMs (Firecracker/E2B/Modal — production-grade isolation, cloud dependency, overkill); SWE-bench's own prebuilt per-task Docker images (not optional if you use SWE-bench — they pin the exact repo state + deps; use them rather than building your own). |

---

## 7. [SPINE] N9-adjacent — Choosing the Comparison Systems

*Standalone context: the project's end state is a benchmark comparing (a) a bare model with no harness, (b) a self-built harness, (c) one or two open-source harnesses — same model(s), same tasks.*

**Baseline A — bare model (mandatory, and define it carefully).** "No harness" can't literally mean nothing (the model has to receive the task somehow). The honest operationalization for coding tasks, used by the SWE-bench authors as the "RAG/oracle-less" baseline: one single API call containing the issue text plus relevant file contents (or a naive retrieval of them), asking for a unified diff; apply the diff; run tests. No loop, no tools, no feedback. Expect very low scores — that gap *is* your headline result ("the harness is worth +X points on the same model").

**Baseline B — mini-swe-agent (mandatory).** ~100 lines, built by the SWE-bench team explicitly to be the standard baseline harness; model-agnostic (bash-only, text-protocol, no native tool calling); powers several 2026 leaderboards. It is the field's reference point, so beating/approaching it is legible to anyone reviewing your repo. ⏱ RE-CHECK: it's on v2 as of 2026 — pin the exact commit you benchmarked and say so.

**Baseline C — smolagents (recommended third column).** Hugging Face's minimal framework whose signature is code-as-action (the model writes Python snippets as its actions). Choosing it makes your comparison span the two live paradigms (tool-calling loop vs. code-action loop) rather than two flavors of the same one. Alternative C's: **OpenHands** (ex-OpenDevin — the feature-heavy production end of the spectrum; interesting contrast but heavyweight to set up and slow to run, so it doubles your compute bill) or **SWE-agent** proper (the original ACI harness; historically important, largely superseded by mini for baseline purposes). If time-boxed, two baselines (A + B) is already a legitimate result; C is the difference between "good project" and "small study."

**Non-negotiable methodology point:** hold the *model* fixed across all systems (or run the full grid over 2 models, one cheap + one mid-tier). A harness comparison with different models per column measures nothing.

---

## 8. [SPINE] N7 + N8 — Tasks, Grading, and Statistics

*Standalone context: an agent harness is being benchmarked against a bare model and existing harnesses. This section chooses the task suite, the grading mechanism, and the statistics that make small-sample numbers honest.*

### 8.1 Task suite (spine pick, coding agent)

**Primary: a fixed subset of 30–50 instances from SWE-bench Lite or SWE-bench Verified.** SWE-bench = real GitHub issues from popular Python repos; the agent gets the repo at a pinned commit + the issue text; success = the repo's own (held-out) unit tests pass after the agent's patch. Verified = the 500-instance human-validated subset; Lite = a 300-instance easier subset; there's also a community "Verified-Mini" (~50). Use the **official per-task Docker images and official grading scripts** — never reimplement grading; the edge cases are why published numbers are comparable.

Two currency caveats, both in your favor but worth stating in the report:
- ⏱ **RE-CHECK / dated-instinct flag:** OpenAI publicly retired SWE-bench Verified for *frontier* evaluation in 2026 (saturation — top models cluster in the high 70s–80s, and successors like SWE-bench Pro / Terminal-Bench 2.0 / ProgramBench now carry the frontier signal). This does **not** hurt you: cheap models are nowhere near saturation, and your experiment is harness-vs-harness at fixed model, not model-vs-frontier. But your README should show you know this, and quote the successor benchmarks by name.
- **Contamination:** these repos and even the benchmark itself are in training data. Standard caveat; affects all your columns equally, so deltas survive.

**Secondary (optional, high credibility-per-hour): 10–15 hand-written original tasks** — small bugs you plant in small codebases, graded by tests you write. Immune to contamination, guaranteed-current, and shows benchmark-design understanding. Keep them alongside, not instead of, SWE-bench (original tasks alone aren't comparable to anything).

### 8.2 [BRANCH] Task-suite alternatives (also = the agent-type decision from §1)

| Suite | Grades | Trade-off |
|---|---|---|
| **Terminal-Bench (2.0 in 2026)** | General terminal tasks; exit codes/diffs, ~15% LLM-judged | The rising coding-adjacent standard; explicitly harness-sensitive (good for you). Slightly more setup than SWE-bench, small judge component. Strong alternate primary if SWE-bench setup fights you. |
| **HumanEval / MBPP-class** | Function synthesis, single-shot | Not agentic — no tools/steps needed, so it can't show harness value. Wrong tool for this project; listed because cheap models will suggest it. |
| **GAIA** (research/Q&A agent path) | Real-world questions needing web + files + multi-step reasoning; exact-match | The canonical general-assistant benchmark; 3 difficulty levels. Costs: needs web tools (reproducibility rot), answer normalization, private test split (you'd use the public validation set). Pick this suite *iff* you override §1 toward a research agent. |
| **tau-bench / tau2** | Customer-service tool-use with a *simulated user*; grades final DB state; reports pass^k reliability | Teaches a genuinely different thing (policy-following, user interaction). Domain-specific; user-simulator adds moving parts. Know it; skip it. |
| **WebArena / OSWorld / AppWorld** | Browser / full-OS / multi-app agents | Famously environment-sensitive and hard to reproduce; screenshot-judge costs. Out of scope. |
| **BFCL v4-class** | Function-*calling* accuracy per se | Tests the model's tool-call formatting, not the harness. Useful diagnostic, not a headline. |

### 8.3 Eval runner (spine)

A script, not a framework: for each `(system, model, task, seed)` → spin task container → run system → collect patch/answer → grade with official script → append one JSON row `{system, model, task, seed, resolved, steps, tokens_in/out, cost, wall_time, termination_reason, trace_path}`. Make runs resumable (skip rows that exist) and parallel-capable (4–8 workers; mind API rate limits). **Branch:** eval orchestration frameworks (HF `lighteval`, UK AISI's `inspect-ai`, W&B Weave evals) exist and are good; for 3 systems × 50 tasks they're more to learn than to gain — but `inspect-ai` is worth a look if this grows.

### 8.4 Statistics that make small numbers honest (spine — this is what most portfolio projects botch)

- **k runs per config** (k=3 minimum; temperature 0 is *not* deterministic across providers). Report **pass@1 averaged over k** (mean success rate), and optionally **pass^k** (solved in *all* k runs — the reliability number tau-bench popularized; the gap between pass@1 and pass^k is itself an interesting finding).
- **Confidence intervals:** with n=50 tasks, a Wilson 95% interval on a 40% success rate is roughly ±13 points. Print intervals on every number; refuse to claim "A beats B" inside overlapping intervals. (Real-world anchor: the DeepSWE study declined to call a 50%-vs-40% difference on n=10 significant, citing exactly this interval. That's the epistemic register your report should hit.)
- **Cost/efficiency axes:** success alone is half the story; report tokens and $ per solved task, and steps-to-solve distributions. "My harness = mini-swe-agent −2 points at 40% of the tokens" is a *better* portfolio result than a bare win.
- **Failure taxonomy:** classify every failure from traces (wrong edit / never reproduced bug / loop-until-step-limit / context overflow / malformed actions / crashed). One table of this signals more understanding than any success number.

**Budget arithmetic (order-of-magnitude, ⏱ RE-CHECK prices):** ~50 tasks × 4 systems (bare, yours, mini, smolagents) × 3 seeds = 600 episodes. A cheap-tier model (Haiku/GPT-mini/Flash class) at ~200–800k tokens per agentic episode ≈ $0.02–0.15/episode ⇒ **roughly $15–90 total**, dominated by whichever system is most verbose. Prompt caching cuts this substantially. Adding one mid-tier model doubles-to-quadruples it. Do a 5-task pilot first and extrapolate before launching the grid.

---

## 9. [SPINE] N9 — The End State, Concretely

The repo that makes this portfolio-grade:

```
your-harness/
├── README.md            # results table UP TOP, then architecture,
│                        # then design decisions incl. rejected branches
├── harness/             # ~300–500 hand-written lines
│   ├── loop.py          # control loop (§4)
│   ├── llm.py           # client (§3)
│   ├── tools.py         # bash/submit + dispatcher (§6)
│   ├── context.py       # truncation/aging policy (§5)
│   └── sandbox.py       # docker exec wrapper (§6)
├── eval/                # runner, grading glue, stats, plots (§8)
├── baselines/           # pinned configs/commits for mini-swe-agent,
│                        # smolagents, bare-model script (§7)
├── traces/              # sample JSONL traces + tiny HTML viewer
└── report.md            # methods, results w/ CIs, failure taxonomy,
                         # ablations, honest limitations
```

What reviewers (human or hiring) actually reward, in order: (1) the results table with error bars and a fixed-model methodology note; (2) the failure-taxonomy table; (3) one or two *ablations* — context policy on/off, native-vs-text tool protocol, plan-then-execute on/off — because ablations are the difference between "built a thing" and "understands the thing"; (4) the rejected-alternatives section (compress the BRANCH tables of this doc into a paragraph each, in your own words); (5) honesty about contamination/saturation caveats (§8.1). A short blog-post version of `report.md` is the highest-leverage optional extra.

---

## 10. [BRANCH] The Whole-Project Alternatives (things this plan rejected at the root)

For completeness — the sideways moves *before* node N1:

- **Fork-and-extend an existing harness** instead of building: fastest to impressive demos; teaches codebase-reading; but your benchmark headline becomes "I tweaked X," and the loop-level understanding never gets forced. Rejected given your stated goal.
- **Build the eval, not the harness** ("benchmark existing harnesses rigorously" as the whole project): genuinely underrated, publishable even (Claw-SWE-Bench is roughly this), and cheaper. Rejected only because you want to build; note that your §8 layer *is* this project embedded in yours.
- **Train/fine-tune instead of scaffold:** different project, different budget (and your T4-Colab constraint rules out anything beyond small LoRAs). The harness project teaches the layer where 2026's practical leverage actually is.
- **Research agent as primary** (GAIA suite, web tools): fully mapped via §1 + §8.2; pick it only if you accept judge-noise and reproducibility rot as the price of a more general-feeling artifact.
- **Product-ify** (UI, streaming, multi-user): résumé-adjacent but orthogonal to understanding; every hour on a TUI is an hour not spent on ablations.

---

## 11. [SPINE] Milestone Checklist (lift this into your task tracker)

- [ ] **M1 (weekend):** raw-HTTP 3-turn tool-call exercise done; then loop + fake tool; then bash-in-tempdir "write 10 primes" works. *(§3–4)*
- [ ] **M2:** Docker sandbox; agent solves 3 hand-made toy bugs end-to-end; JSONL traces + limits in place. *(§5–6)*
- [ ] **M3:** SWE-bench official images running locally; your harness completes 5 real instances (any score); grading via official scripts. *(§8.1)* ⏱ RE-CHECK current SWE-bench tooling docs here.
- [ ] **M4:** eval runner resumable + parallel; bare-model baseline scripted; 5-task pilot across all systems; extrapolate budget. *(§7–8.3)*
- [ ] **M5:** full grid (≈50 tasks × systems × 3 seeds); stats + CIs + failure taxonomy. *(§8.4)*
- [ ] **M6:** one or two ablations; README/report; publish. *(§9)*
- [ ] Standing rule throughout: **agent core is hand-written; AI assists everywhere else.** *(§0)*

## 12. Dated-Instinct Ledger (where my priors needed correcting, per the August 2026 search pass)

1. SWE-bench Verified is no longer a frontier-differentiating benchmark (OpenAI retired it for that purpose in 2026); successors: SWE-bench Pro, Terminal-Bench 2.0, ProgramBench. Fine for your cheap-model harness study; frame accordingly.
2. mini-swe-agent is on **v2** and now scores >74% Verified with strong models — higher than older write-ups suggest; pin your commit.
3. MCP has fully won the tool-integration standards question (Linux Foundation / Agentic AI Foundation stewardship since Dec 2025, all major vendors); it complements rather than replaces function calling.
4. The "minimal harness ≥ complex harness (with strong models)" result has hardened from anecdote into a repeated 2026 research finding — it now justifies your bash-only spine as a *choice* rather than a simplification.
5. The multi-agent hype has visibly cooled in 2026 commentary ("single-agent products dressed as multi-agent"); skipping it is now the defensible default, not a gap.
