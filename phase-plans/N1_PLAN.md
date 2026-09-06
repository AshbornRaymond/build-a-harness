# Phase Plan — N1: Fundamentals (Raw HTTP, Tokens, Tool-Calling Wire Format)

> Companion to [CLAUDE.md](../CLAUDE.md), [BUILD_STEPS.md](../BUILD_STEPS.md)
> (Phase 0 + Phase N1 sections), [llm-harness-plan_1.md](../llm-harness-plan_1.md)
> §3, and [harness-vocabulary-primer.md](../harness-vocabulary-primer.md)
> Units 6–12 (already covers most core terminology — cross-referenced below
> rather than re-written).
>
> Planned: 2026-09-06. Read order followed: CLAUDE.md → BUILD_STEPS.md →
> llm-harness-plan_1.md §3/§12 → repo state → independent concept-map pass →
> targeted web verification.

---

## Step 1 — Progress Audit

**Repo state verified directly** (`ls`, no `.git` present):

```
CLAUDE.md, CLAUDE_legacy_gsm8k_plan.md, BUILD_STEPS.md,
llm-harness-plan_1.md, harness-vocabulary-primer.md,
PHASE_PLANNER_PROMPT.md, test.py
```

No `harness/`, `eval/`, `baselines/`, `traces/`, `docs/`, or `scratch/`
directories exist. No `pyproject.toml`/`requirements.txt`/venv. No `.gitignore`.
No `.env`. Not a git repository at all.

### Phase 0 (Repo & Environment Setup) — **incomplete**, checkboxes are honest

| Step | Status | Evidence |
|---|---|---|
| 0.1 folder skeleton | ❌ not done | none of `harness/eval/baselines/traces/docs` exist |
| 0.2 `git init` + `.gitignore` | ❌ not done | `git status` → "not a git repository" |
| 0.3 package manager decision | ❌ not made | no venv, no lockfile, no `pyproject.toml` |
| 0.4 environment + manifest | ❌ not done | — |
| 0.5 provider API key as env var | ❌ **not done, and actively violated** | [test.py:7](../test.py#L7) hardcodes a live OpenRouter key as the `os.getenv` fallback default — the opposite of "never hardcode it" |
| 0.6 `.env`/dotenv so the key never touches a committed file | ❌ not done | same finding — there's no `.env`, the key is in a plain `.py` file with no `.gitignore` to protect it if `git init` happens next |
| 0.7 curl smoke-test before writing Python | unverified, moot | test.py itself proves the key round-trips through OpenRouter successfully (it got real completions + tool calls back), so connectivity is empirically established — but not via the prescribed curl-first method |

BUILD_STEPS.md's Phase 0 checkboxes are all unchecked — that matches reality, no correction needed.

**Action taken by this plan:** flagged the leaked key to the user directly in
conversation (rotate it, never hardcode a fallback again). Track A below
folds the minimum Phase 0 steps needed to unblock N1 cleanly (env var, repo
skeleton, `.gitignore`) — this is the one deliberate, narrow exception to
"scope Track A to exactly one phase," because N1 cannot be done safely
without them and CLAUDE.md's own Phase 0 is a prerequisite, not a peer.

### Phase N1 (Fundamentals) — **incomplete**

| Step | Status | Evidence |
|---|---|---|
| 1.1 single hardcoded-prompt call, inspect every response field | ❌ not done | no `scratch/n1_single_call.py`; test.py never prints/discusses `usage.input_tokens`, `stop_reason`, `id`, etc. |
| 1.2 temp 0 vs 1, diff outputs | ❌ not done | test.py has no temperature parameter at all (provider default used, unexamined) |
| 1.3 manual 2-turn conversation stitching | ❌ not done | never attempted |
| 1.4 deliberately truncate history, observe context loss | ❌ not done | never attempted |
| 1.5–1.6 hand-defined tool schema, inspect raw tool-call block | ⚠️ partial | test.py *does* define a `bash` tool schema and send it (lines 19–37), and does receive back a real `tool_calls` block — but the schema/response were never manually inspected field-by-field, they're piped straight into automated handling |
| 1.7 hand-fabricate a tool result, confirm model incorporates it | ⚠️ **short-circuited, not satisfied** | test.py's `emulate_bash()` (lines 39–48) special-cases the exact prompt ("`*.py`" + "wc -l"/"count") and returns a **fabricated count from Python's own `glob.glob`**, not from letting the model's real bash command run and then hand-crafting the result. This defeats the point of 1.7: the exercise is "compute the fake result *yourself*, matching the schema, and watch the model use it" — not "silently intercept and answer the user's actual question in Python before the model even gets a real observation." |
| 1.8 hand-craft an *invalid* tool result, observe model reaction | ❌ not done | never attempted |
| 1.9 `docs/n1_notes.md` write-up | ❌ not done | no `docs/` dir |

**Conclusion:** test.py is useful evidence that (a) the OpenRouter key works,
(b) the OpenAI-compatible tool-calling wire shape round-trips end-to-end
with a live model. It is **not** the N1 exercise and shouldn't be mistaken
for it — it was AI-authored, skips 1.1–1.4 and 1.8–1.9 entirely, and its
one nod to "tool execution" (`emulate_bash`) actually hides the wire format
behind a hardcoded shortcut rather than exercising it. This matches your own
note: you can see it *works* but aren't solid on *why*. Keep the file as a
working reference (rename it, don't delete — see Track A step N1.0c), but
the real N1 exercise still needs to happen, by hand, from an empty script.

**Single next phase to plan (Step 2 of the audit instructions):** the
boundary is unambiguous — Phase 0 has zero real progress and N1 has partial-
but-not-satisfying progress; nothing downstream (N2+) has any basis to stand
on yet. This matches your stated `CURRENT_PHASE: N1`. Planned below.

---

## Track A — Build Steps

*Cross-references [BUILD_STEPS.md](../BUILD_STEPS.md) Phase 0 (0.1–0.7) and
Phase N1 (1.1–1.9). Sharpened into hour-or-less steps with concrete "done
when" tests. None of N1's files are on the hand-write-only list
(`loop.py`/`llm.py`/`tools.py`/`context.py`), but the entire point of this
phase is *you* building the mental model — writing it yourself is strongly
recommended, not just tolerated. An assistant reading your code afterward to
sanity-check field names is fine; an assistant generating the script is not
(it already happened once, that's why this phase isn't actually done).*

### N1.0 — Minimum Phase 0 prerequisite (not full Phase 0, just the unblockers)

- [ ] **N1.0a** `[DECISION]` Rotate the leaked OpenRouter key at
      openrouter.ai (Settings → Keys) — the current one has been sitting in
      a plaintext file. Done when a new key exists and the old one shows
      revoked in the dashboard.
- [x] **N1.0b** `[AI-OK]` Create `harness/ eval/ baselines/ traces/ docs/
      scratch/` as empty dirs (BUILD_STEPS 0.1, + `scratch/` which N1 itself
      needs). `git init`, add `.gitignore` with at minimum `.env`,
      `__pycache__/`, `.venv/` (BUILD_STEPS 0.2). Done when `git status`
      shows a clean initialized repo and none of these dirs are empty-tree
      artifacts of a bad path.
- [x] **N1.0c** `[AI-OK]` Move `test.py` → `scratch/n0_openrouter_smoke_test.py`
      (rename, don't delete — it's a real working artifact) and delete the
      hardcoded key fallback, replacing it with `os.environ["OPENROUTER_API_KEY"]`
      (hard fail if unset, no default). Done when the file only reads the
      key from the environment and running it without the env var set
      raises `KeyError` instead of silently using a stale/leaked key.
- [x] **N1.0d** `[DECISION]` Pick venv tool (BUILD_STEPS 0.3 — `uv` recommended,
      any is fine) and create a minimal `pyproject.toml`/`requirements.txt`
      with just `requests` and `python-dotenv` for now. Done when
      `python -c "import requests"` works inside the activated environment.
- [x] **N1.0e** `[AI-OK]` Set `OPENROUTER_API_KEY` (or `ANTHROPIC_API_KEY`,
      see N1.1-DECISION below) via `.env` + `python-dotenv`, confirm it loads.
      Done when `python -c "import os,dotenv; dotenv.load_dotenv();
      print(bool(os.environ.get('...')))"` prints `True`.

### N1.1 — Single call, read every field

- [ ] **N1.1** `[DECISION]` Provider for the exercise: BUILD_STEPS recommends
      **Anthropic direct** (raw Messages API — you already have some
      familiarity per CLAUDE.md's background-calibration note). The
      alternative is continuing with OpenRouter/Chat-Completions-shape since
      you already have a working key and test.py proved it. **Recommendation:
      do the exercise against Anthropic's native Messages API even though
      you'll keep OpenRouter around for later multi-model runs** — the two
      wire shapes differ in exactly the places that matter for N1 (see Track
      B "system field" and "tool_result role" gotchas below), and seeing the
      *native* shape once is the actual point before you let LiteLLM/OpenRouter
      hide it again in N2. Get an `ANTHROPIC_API_KEY` if you don't have one.
- [ ] **N1.2** `[HAND-WRITE, by hand not by assistant]` Write
      `scratch/n1_single_call.py`: one `requests.post` to
      `https://api.anthropic.com/v1/messages` with headers
      `x-api-key`, `anthropic-version`, `content-type: application/json`,
      body `{model, max_tokens, system, messages: [{role:"user", content:"..."}]}`.
      Print the full raw JSON response (`json.dumps(data, indent=2)`), not
      just the text. Done when you can point to, in the printed output:
      `usage.input_tokens`, `usage.output_tokens`, `stop_reason`, `model`, `id`,
      and explain each without looking anything up.
- [ ] **N1.3** Re-run at `temperature: 0` twice and `temperature: 1` twice
      (same prompt, ask something with room for variation — not "2+2").
      Diff the four outputs. Done when you've written one sentence (can be
      in a comment) stating what you observed about temp-0 variability, if
      any — this is your own empirical basis for D9's "k≥3 runs" rule, not
      something to take on faith.

### N1.2 — Statelessness, by hand

- [ ] **N1.4** Extend the script (or a new one) to send a 3-message array:
      `[user, assistant, user]`, where the assistant message is the **literal
      text you got back** from N1.2, copy-pasted — not re-generated, not
      paraphrased. Done when turn 3's response coherently references
      something only turn 1 established, proving the model only "knows" what
      you resent.
- [ ] **N1.5** Deliberately break it: resend the same 3-turn array but
      **omit the first user message**, keeping only
      `[assistant, user]`. Observe the model either lose context, get
      confused about what "it" refers to, or (for Anthropic specifically)
      reject the request for not starting with a `user` role — either
      outcome is the point. Done when you've noted which failure mode you
      actually saw.

### N1.3 — Tool calling, end to end, by hand

- [ ] **N1.6** Define one tool schema by hand as a Python dict — reuse
      `bash: {cmd: string}` from the plan, or invent a toy `get_weather(city)`
      to keep it dead simple. Match Anthropic's exact field name:
      `input_schema` (not `parameters` — that's the OpenAI-family name; see
      Track B). Send a message likely to trigger it. Done when the response's
      `stop_reason` is `tool_use` and `content` contains a block with
      `type: "tool_use"`.
- [ ] **N1.7** Print and read that block's exact shape: `id`, `name`, `input`.
      Done when you can state, without looking it up, which field you'll
      need to echo back in the next turn and why (the `id` — it's how the
      API matches your result to its request).
- [ ] **N1.8** By hand, fabricate a plausible tool result — **do not let it
      actually run bash yet, and do not silently intercept the user's real
      question in Python** the way test.py's `emulate_bash` did. Construct
      the Anthropic-shaped follow-up: append the assistant's tool-use message
      verbatim, then a **new `user`-role message** whose `content` is a list
      containing one block: `{"type": "tool_result", "tool_use_id": <the id
      from N1.7>, "content": "<your fabricated result>"}`. Send turn 3. Done
      when the model's final answer coherently uses your fabricated number/fact
      — this confirms you understand tool results are a `user`-role content
      block in Anthropic's shape, not a `role: "tool"` message (that's the
      OpenAI/OpenRouter convention test.py used, correctly, for *that* shape).
- [ ] **N1.9** Repeat N1.8 but hand-craft an **invalid** tool result — wrong
      key name, or a JSON string where the tool's schema implied structured
      data. Done when you've observed and written down how the model reacts
      (ignores it, asks for clarification, hallucinates past it) — this is a
      preview of the malformed-observation handling N3 will need.

### N1.4 — Write it down

- [ ] **N1.10** `[AI-OK to polish, HAND-WRITE the content]` Write
      `docs/n1_notes.md`, 10–15 lines covering: request shape, response
      shape, tool-call shape, what statelessness meant in practice once you
      broke it yourself (N1.5), what temp 0 vs 1 actually looked like
      (N1.3), and the one or two wire-format gotchas from Track B that bit
      you. Done when a future-you (or a reviewer) can read it and understand
      the wire format without opening the raw JSON again.

**Phase done when:** you've held a 3-turn conversation with a hand-executed
tool call using only `requests` against Anthropic's native API, under an
hour of *active* work (excluding the Phase 0 setup above), and can explain
every field in the request/response JSON without looking it up — matching
BUILD_STEPS.md's original N1 "done when," now actually satisfied rather than
approximated by test.py.

---

## Track B — Broaden the Knowledge

*Independent concept-map pass done first (own knowledge + WebSearch),
**then** reconciled against llm-harness-plan_1.md §3/§12 and
harness-vocabulary-primer.md Units 6–12. Items already covered well by the
vocabulary primer are cross-referenced rather than re-explained — read that
file for the base definitions; this section adds what's missing, contested,
or has moved since either doc was written.*

### Concept map — in-scope for the build vs. know-it-exists

**In scope for N1/N2 (you'll touch these directly):**
- HTTP request/response, headers, status codes, JSON body — primer Unit 3
- Statelessness / full-history resend — primer Unit 4
- Messages array, roles (`system`/`user`/`assistant`) — primer Unit 7
- **System prompt placement differs by provider** — Anthropic: top-level
  `system` string field, *not* a message. OpenAI/OpenRouter (Chat
  Completions shape): a message with `role: "system"` inside the `messages`
  array. This is a real, easy-to-get-wrong difference the plan's schematic
  (which shows a Anthropic-flavored shape with an OpenAI-esque `tool_calls`
  key) blends together — worth noting explicitly since you'll hit both
  shapes (Anthropic direct now, OpenRouter/LiteLLM later).
- Tool/function schemas as a JSON-Schema subset — field name differs:
  Anthropic `input_schema`, OpenAI-family `parameters`. Both wrap a
  standard JSON Schema object (`type`, `properties`, `required`).
- Tool call response shape — Anthropic: `content` block with
  `type: "tool_use"`, fields `id`/`name`/`input`. OpenAI-family: top-level
  `tool_calls` array, fields `id`/`function.name`/`function.arguments`
  (**arguments is a JSON-encoded *string*, not a parsed object** — test.py
  correctly does `json.loads(tool_call["function"]["arguments"])` at line
  73; this is a common first-timer bug when people forget the extra parse).
- Tool result / observation message — Anthropic: new `user`-role message,
  `content` list with a `{"type":"tool_result","tool_use_id":...}` block.
  OpenAI-family: new message with `role:"tool"`, `tool_call_id`, plain
  string `content` (this is what test.py does, correctly, for that shape).
  **These are genuinely different message shapes, not just field renames** —
  the most important single gotcha for this phase.
- `stop_reason` (Anthropic) / `finish_reason` (OpenAI-family) values:
  `end_turn`/`stop`, `tool_use`/`tool_calls`, `max_tokens`/`length`,
  `stop_sequence`/`stop`.
- **Parallel tool calls** — not in the plan's 3-BRANCH table at all, but
  directly relevant to D3 ("one action per turn"): Anthropic's default
  behavior is to allow *multiple* `tool_use` blocks in a single assistant
  turn (confirmed current via platform.claude.com/docs, Sept 2026 search).
  If you don't want that, you must explicitly pass
  `tool_choice: {"type": "auto", "disable_parallel_tool_use": true}`.
  OpenAI-family has an analogous `parallel_tool_calls: false`. **This means
  D3's "one action per turn" isn't free — it's a parameter you have to set,
  or the loop in N3 needs to handle a list of tool calls in one turn even
  though the spine wants to treat them as one.** Worth deciding explicitly
  in N3, flagged here since it's a wire-format-level fact you'll only notice
  by reading the docs closely (or by getting bitten by it).
- Tokens: BPE/subword units, ~0.75 words/token heuristic — primer Unit 9.
  Provider tokenizers differ (OpenAI's `tiktoken`, Anthropic's own, exposed
  via a `count_tokens` endpoint rather than a public offline library) — so
  "N tokens" for the same string is provider-specific, not universal.
- Context window — primer Unit 10. **Numbers worth updating**: as of this
  search pass (Sept 2026, via aggregator sites, not primary docs — re-verify
  against platform.claude.com/docs and platform.openai.com/docs before
  citing in your report), Claude Sonnet 5 / Opus 5 ship ~1M-token context
  (Haiku 4.5 stays at 200K), GPT-5.x sits around 128K–256K depending on
  variant, Gemini 3.x reaches up to 2M. The plan's "200k–1M+" line is in the
  right ballpark for Claude specifically but not a safe generalization
  across providers — don't repeat it as a flat fact in your own report
  without a per-model table.
- `temperature`, `max_tokens` — primer Unit 11. One addition: **`max_tokens`
  truncating mid-response can cut a tool call's JSON arguments in half**,
  producing a `stop_reason: "max_tokens"` with an unparseable partial
  `tool_use.input` — a real failure mode, not hypothetical, worth trying to
  provoke once (set `max_tokens` absurdly low against a tool-triggering
  prompt) so you recognize it later in N3.
- Determinism at temp 0 — "near-deterministic, not deterministic" holds up:
  batched GPU inference and (for MoE models) expert-routing nondeterminism
  mean identical requests can still diverge slightly. This is the empirical
  basis for D9.
- Rate limits, 429s, `Retry-After` — primer Unit 12. Not needed until N2's
  retry logic, but worth recognizing the header now if you see one.
- Prompt caching — primer Unit 12 covers the concept; mechanically,
  Anthropic requires explicit `cache_control: {"type": "ephemeral"}`
  breakpoints in the request, while OpenAI-family APIs cache automatically
  for prefixes ≥1024 tokens with no markup needed. Not used in N1, matters a
  lot once N2's `call_llm` starts re-sending the same system prompt/tool
  schemas every step.

**Know it exists, out of scope for this build (per D1/D3/D4's minimalism):**
- Streaming (SSE) — responses arrive as incremental chunks including
  partial tool-call-argument deltas that must be reassembled. Real added
  complexity for a correctness-focused eval harness; the project can use
  non-streaming calls throughout and lose nothing but perceived latency.
- Structured outputs / JSON mode (`response_format: {"type":"json_schema"}`)
  — a different mechanism from tool calling, guarantees schema-conformant
  prose output; not needed since tool calling already gives you structure.
- Batch APIs (Anthropic Message Batches, OpenAI Batch API) — async, ~50%
  cheaper, minutes-to-24h turnaround; irrelevant for a synchronous agent loop.
- Idempotency keys — an OpenAI-recommended header for safely retrying a
  POST that may have already succeeded server-side; relevant if N2's retry
  logic gets sophisticated, not for N1.
- Extended thinking / reasoning-token blocks (Claude extended thinking,
  OpenAI reasoning models) — when combined with tool use, some providers
  require the thinking block to be echoed back verbatim alongside the tool
  result on the next turn, or the API rejects the request. A real gotcha if
  you later benchmark a reasoning-tier model; irrelevant for the cheap
  non-reasoning models this project targets first.
- Realtime/websocket APIs, multimodal (vision/audio) content blocks,
  citations/document blocks — not used by a text-only coding agent.
- MCP (Model Context Protocol) — primer Unit 29 covers it; per the plan's
  §12 ledger it's now the dominant *tool-integration* standard, but it's a
  layer *above* raw function calling (a way to serve tool definitions over a
  protocol), not a replacement for understanding the wire format itself.

### Alternative approaches beyond the plan's 3-BRANCH table

The plan's table (raw HTTP / official SDK / LiteLLM / local models / agent
SDKs — *prior-plan-sourced*, all still accurate as of this pass) omits two
points on the spectrum worth naming explicitly:

- **Hosted OpenAI-compatible aggregator (OpenRouter), used directly with
  `requests`** — exactly what test.py does. This sits between "official SDK"
  and "LiteLLM": you get one fixed wire shape (Chat Completions) and access
  to 400+ models with no client library at all, but you're depending on
  OpenRouter's own normalization rather than a provider's native shape or a
  purpose-built abstraction library. Trade-off worth knowing before N2:
  OpenRouter's **free-tier models are rate-limited, lower-priority, and can
  disappear/change silently** (confirmed current via Sept 2026 search) — a
  real reproducibility risk for N8's benchmark grid if you standardize on
  a `:free` model tag long-term rather than a paid, versioned one.
- **curl-only, no Python at all** — even more raw than `requests`; BUILD_STEPS
  allows it explicitly ("no SDK, no abstraction... nothing but
  `requests`/`curl`") but nobody in the current docs actually does it. Worth
  trying for just the first single-call exercise (N1.2) — with `requests`,
  header/auth handling is invisible; with raw `curl -H`, you type every
  header by hand once, which is a genuinely different (better, for this
  specific learning goal) kind of friction.

### Underlying theory / primary sources

- **ReAct** — Yao et al. 2022, *"ReAct: Synergizing Reasoning and Acting in
  Language Models,"* arXiv:2210.03629. Cited in the plan for N3, but it's
  the conceptual ancestor of "tool call = structured action, response =
  observation" that N1's exercise is teaching you to do by hand.
- **Function calling's origin as a product feature** — OpenAI's June 2023
  function-calling launch is the historical point where "emit structured
  JSON instead of prose" became a first-class, fine-tuned API capability
  rather than a prompt-engineering trick; useful context for *why* this
  wire format exists at all rather than everyone just parsing prose.
- **BPE tokenization** — Sennrich, Haddow, Birch 2015, *"Neural Machine
  Translation of Rare Words with Subword Units,"* the paper that brought
  byte-pair encoding into NLP; underlies every modern LLM tokenizer
  (`tiktoken`, Anthropic's tokenizer, SentencePiece variants).
- **JSON Schema spec** (json-schema.org) — the actual spec that
  `input_schema`/`parameters` are a constrained subset of; useful if a tool
  schema ever behaves unexpectedly and you need to know what's "spec" vs.
  provider-specific extension.
- **Anthropic Messages API reference** (platform.claude.com/docs) and
  **OpenAI Responses API migration guide**
  (developers.openai.com/api/docs/guides/migrate-to-responses) — primary,
  current docs. Note: OpenAI now recommends the newer **Responses API**
  over Chat Completions for new projects (confirmed current, Sept 2026
  search) — Chat Completions remains fully supported indefinitely, and
  OpenRouter/LiteLLM both still speak the Chat-Completions shape, so this
  doesn't block anything here, but it's worth knowing the OpenAI-native
  "recommended default" has shifted since the plan was written in August
  2026 and don't be surprised if OpenAI's own docs increasingly favor
  Responses-API examples over Chat-Completions ones going forward.

### Common failure modes and misconceptions

- Believing the model "remembers" prior turns without you resending them —
  the entire point of N1.4/N1.5.
- Confusing `max_tokens` (response-length cap) with the context window
  (total input+output cap) — two different numbers, two different failure
  modes.
- Treating temp-0 as bitwise-deterministic and being confused when a report
  can't reproduce a run exactly — it's "near," not exact, by design of how
  the model is served.
- Assuming the API validates tool-call arguments against your schema before
  handing them to you — it doesn't strictly enforce this; malformed
  `input`/`arguments` reach your code, which is exactly why N3.6's
  malformed-action handling exists downstream.
- Forgetting to append the assistant's tool-use message to history verbatim
  (with its exact `id`) before appending your tool result — the API needs
  that `id` round-tripped to match request to result; skip it and the next
  call errors or the model loses track of which call your result answers.
- Anthropic-specific: sending a tool result as a `role:"tool"` message
  (correct for OpenAI-family, wrong for Anthropic) — the API will reject it
  or behave unpredictably; it must be a `user`-role message containing a
  `tool_result` content block.
- Not reading `usage` on every call and being surprised later, in N2/N8,
  when cost tracking depends on numbers you never looked at during N1.

### What production/frontier systems do differently (and why that's out of scope here)

- Provider "agent SDKs" (OpenAI Agents SDK, Claude Agent SDK) wrap this
  entire request/tool-result/retry loop for you — explicitly rejected by
  CLAUDE.md's hard rule and the plan's 3-BRANCH table ("they *are* the
  harness; using one defeats the project").
- Production systems cache the system prompt + tool schemas aggressively
  across every step of an agentic episode (byte-identical every turn) —
  the single biggest real-world cost lever for exactly the kind of loop
  this project builds; deferred to N2/N5 here, but worth knowing it exists
  the moment you notice how much of the request is identical turn-to-turn.
- Production systems stream tool-call argument deltas rather than waiting
  for a full response — a latency optimization irrelevant to a
  correctness-and-cost-focused eval harness; skip it, as noted above.

### Terminology glossary

Base definitions for LLM/model/inference, prompt/messages/roles, tool
call/tool result/observation, token, context window, temperature/max_tokens/
deterministic, and prompt caching/rate limits/retry-backoff are already
precisely covered in
[harness-vocabulary-primer.md](../harness-vocabulary-primer.md) Units 6–12 —
read there rather than here. Terms this phase adds that aren't in that
primer:

- **`stop_reason` / `finish_reason`** — the field telling you *why* the
  model stopped generating this turn (finished naturally, hit a tool call,
  hit the length cap, hit a stop sequence). You branch your loop logic on
  this value in N3.
- **`tool_choice`** — a request parameter controlling whether the model
  *must* call a tool, *may* call one (`auto`), or is forbidden from calling
  any (`none`) — and, per the parallel-tool-calls finding above, whether it
  may call more than one per turn.
- **Parallel tool calls** — a single assistant turn containing more than
  one tool-call block; allowed by default on both major providers, must be
  explicitly disabled if your loop design (D3) assumes one action per step.
- **JSON Schema** — the underlying spec that tool-parameter schemas are a
  constrained subset of (`type`, `properties`, `required`, etc.).
- **BPE (byte-pair encoding)** — the subword tokenization algorithm behind
  most modern LLM tokenizers; the mechanism that makes "~0.75 words per
  token" an approximation rather than an exact rule (common words often get
  one token, rare/foreign words fragment into several).

### Further reading (optional, self-paced)

- Anthropic Messages API reference & tool-use guide — platform.claude.com/docs
- OpenAI Responses API migration guide — developers.openai.com/api/docs/guides/migrate-to-responses
- ReAct paper — arXiv:2210.03629
- `tiktoken` repo (reference BPE tokenizer implementation) — github.com/openai/tiktoken
- mini-swe-agent source — read once, per CLAUDE.md's own recommendation,
  *closed* before you write N3's loop from scratch. Not needed for N1
  itself, but the natural next thing to read once this phase is done.

---

## Open Decisions

These are the `[DECISION]` points from Track A you still need to make —
none block starting, but pick before or during the relevant step:

1. **N1.0a** — rotate the leaked OpenRouter key now, before doing anything
   else with this repo (including `git init` — don't let the old key ever
   enter history).
2. **N1.0d** — venv/package manager: `uv` vs plain `venv`+`pip` vs `poetry`.
   Recommended: `uv`. Any choice is fine, just make it once.
3. **N1.1** — provider for the hand-written exercise: Anthropic direct
   (recommended, exposes the wire-format differences that matter) vs.
   continuing on OpenRouter (faster since the key already works, but hides
   exactly the Anthropic-vs-OpenAI shape differences this phase exists to
   teach). Recommendation stated above; you may override it.
4. (Downstream, not blocking N1, noted so it isn't lost) — whether N3's
   control loop assumes strictly one tool call per turn (per D3) or handles
   a list — depends on whether you set `disable_parallel_tool_use`/
   `parallel_tool_calls:false` in N2, a decision this phase's research
   surfaced but N2/N3 will actually make.
