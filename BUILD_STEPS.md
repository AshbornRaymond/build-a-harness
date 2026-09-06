# BUILD_STEPS.md — Granular Execution Plan

> Companion to [CLAUDE.md](CLAUDE.md) (live status/decisions) and
> [llm-harness-plan_1.md](llm-harness-plan_1.md) (design-space rationale).
> This file exists for one purpose: turn the N1→N9 spine into steps small
> enough that you never sit down not knowing exactly what to type next.
>
> **Tags on every step:**
> - `[HAND-WRITE]` — you write this yourself, no coding assistant, per the
>   project's one hard rule. Core files: `loop.py`, `llm.py`, `tools.py`,
>   `context.py`.
> - `[AI-OK]` — Dockerfiles, eval plumbing, plotting, README, baseline glue,
>   rubber-ducking. Delegate freely.
> - `[DECISION]` — a fork where you pick an option before continuing; the
>   recommended pick is bolded, alternatives are in llm-harness-plan_1.md if
>   you want to reconsider.
>
> Check boxes off as you go — this file is the task tracker, CLAUDE.md's
> Status section is the compressed summary you update after each milestone.

---

## Phase 0 — Repo & Environment Setup (before N1)

Nothing here is graded or clever; it just has to exist before step 1 of the
real work.

- [x] 0.1 `[AI-OK]` Create the folder skeleton (empty dirs are fine, files come later):
  ```
  harness/  eval/  baselines/  traces/  docs/  scratch/
  ```
- [x] 0.2 `[AI-OK]` `git init`, add a `.gitignore` (Python: `__pycache__/`,
      `.venv/`, `*.pyc`, `.env`, `traces/*.jsonl` if you don't want raw
      traces in git — decide now, not after you've committed API keys).
- [x] 0.3 `[DECISION]` Package/venv manager: **`uv`** (fast, single binary,
      2026 default) vs. plain `venv`+`pip` vs. `poetry`. Any is fine; pick
      one and don't relitigate.
- [x] 0.4 `[AI-OK]` Initialize the environment and a `pyproject.toml` (or
      `requirements.txt`) with zero deps yet — you'll add deps one at a time
      as each phase needs them, not all upfront.
- [x] 0.5 `[DECISION]` Pick your model provider(s) for N1's raw-HTTP exercise.
      **Anthropic** (you already have familiarity) is the simplest single
      target. Get an API key, store it as an environment variable
      (`ANTHROPIC_API_KEY`), never hardcode it, add `.env` to `.gitignore`.
- [x] 0.6 `[AI-OK]` Install `python-dotenv` (or just export the var in your
      shell profile) so the key loads without ever touching a file you'd
      commit.
- [x] 0.7 Sanity check: `curl` a trivial authenticated request (e.g. list
      models, or a docs-provided smoke-test curl) to confirm the key works
      *before* writing any Python. This isolates "auth problem" from "code
      problem" for everything that follows.

**Done when:** empty repo skeleton exists, venv activates, API key is set
and verified reachable via one curl call.

---

## Phase N1 — Fundamentals: Raw HTTP, Tokens, Tool-Calling Wire Format

*Goal: demystify what an "LLM call" and "tool call" actually are, using
nothing but `requests`/`curl`. No SDK, no abstraction. §3 of the plan.*

- [ ] 1.1 Write `scratch/n1_single_call.py`: one `requests.post` to the
      Messages API with a hardcoded system prompt + one user message. Print
      the raw JSON response. **Read every field** — don't just print
      `.content[0].text`; look at `usage.input_tokens`,
      `usage.output_tokens`, `stop_reason`, `model`, `id`.
- [ ] 1.2 Change `temperature` to 0 and 1, run the same prompt twice at each,
      diff the outputs. Confirms "near-deterministic, not deterministic" —
      this is the empirical basis for D9's k≥3 runs requirement later.
- [ ] 1.3 Extend to a 2-turn conversation: manually build the `messages`
      list as `[user, assistant, user]` where the assistant turn is the
      *actual text you got back* from step 1.1 (copy-pasted, not
      re-generated). Confirms statelessness — nothing works unless you
      resend it yourself.
- [ ] 1.4 Deliberately break it: truncate the resent history to *omit* the
      first user turn and see the model lose context. This is the "why
      context management exists" moment — note it, you'll cite it later.
- [ ] 1.5 Define one tool schema by hand as a Python dict — e.g. a fake
      `get_weather(city: string)` — matching the API's `tools` field shape.
      Send a request with `tools=[...]` and a user message that should
      trigger it ("what's the weather in Tokyo?").
- [ ] 1.6 Inspect the response: find the tool-call block (structured JSON,
      not prose). Note the exact field names (`tool_use`/`function_call`
      block, `id`, `name`, `input`) — you'll need these exact shapes in N2.
- [ ] 1.7 **By hand**, fabricate a plausible tool result (e.g.
      `{"temp_c": 18, "condition": "cloudy"}`), construct the correctly-typed
      tool-result message per the API docs, append it, send turn 3. Confirm
      the model incorporates it into a final prose answer.
- [ ] 1.8 Repeat 1.5–1.7 but pass an **invalid** tool result (wrong schema,
      or a string where JSON was expected) and observe how the model reacts.
      This previews the "malformed action" handling you'll build in N3.
- [ ] 1.9 Write 10–15 lines in `docs/n1_notes.md` (`[AI-OK]` to polish,
      `[HAND-WRITE]` the actual understanding) capturing: request shape,
      response shape, tool-call shape, what statelessness means in practice,
      what you saw at temp 0 vs 1.

**Done when:** you've held a 3-turn conversation with a hand-executed tool
call using only `requests`, under an hour of active work, and can explain
every field in the request/response JSON without looking it up.

---

## Phase N2 — LLM Client (`harness/llm.py`)

*Goal: one function that hides provider wire-format differences behind a
stable internal shape. §3-BRANCH. This file is `[HAND-WRITE]`.*

- [ ] 2.1 `[DECISION]` Client layer: **LiteLLM** (or OpenAI SDK pointed at
      OpenRouter) so swapping models later is a string change. Installing
      the library is `[AI-OK]`; the wrapper code around it is
      `[HAND-WRITE]`.
- [ ] 2.2 Design the internal response shape *before* writing code — a
      plain dataclass/dict with fields you decide now, e.g.:
      `text`, `tool_calls: list[{name, args, id}]`, `stop_reason`,
      `input_tokens`, `output_tokens`, `cost_usd`. Write this down in a
      comment or docstring first; it's the contract every other module
      depends on.
- [ ] 2.3 `[HAND-WRITE]` Implement `call_llm(messages, tools, model,
      temperature=0.0, max_tokens=4096) -> LLMResponse` wrapping the
      chosen client library, normalizing its provider-specific response
      into your dataclass from 2.2.
- [ ] 2.4 `[HAND-WRITE]` Add a small hardcoded pricing table
      (`{model: (usd_per_1k_input, usd_per_1k_output)}`) and compute
      `cost_usd` per call from token counts. ⏱ re-check current prices
      before trusting this for the budget math in N8.
- [ ] 2.5 `[HAND-WRITE]` Add retry-with-exponential-backoff on 429/5xx
      (transient errors only — do not retry on 4xx client errors like bad
      schema, that's a bug not a transient failure).
- [ ] 2.6 `[HAND-WRITE]` Decide and implement error behavior for permanent
      failures (auth error, invalid model name): raise, don't silently
      swallow — the loop in N3 needs to distinguish "tool failed" from
      "LLM call itself failed."
- [ ] 2.7 Manual test script (`scratch/n2_test_client.py`, `[AI-OK]` to
      scaffold): call `call_llm` with the same tool schema from N1.5,
      confirm the normalized `tool_calls` field matches what you saw in the
      raw JSON. This is your regression check before N3 depends on it.
- [ ] 2.8 Swap `model=` to a second provider/model string, rerun 2.7,
      confirm the *normalized* output shape is identical even though the
      raw wire format differed. This is the actual point of N2 — prove it
      to yourself, don't assume it.

**Done when:** `call_llm(messages, tools, model)` returns a stable shape
regardless of which model string you pass, with cost and token counts
attached.

---

## Phase N3 — Control Loop (`harness/loop.py`)

*Goal: the ~50-line heart of the project. §4. Entirely `[HAND-WRITE]` —
this is the file the whole project exists to make you build yourself.*

Build it in layers, testing each before adding the next — do not write the
whole loop in one sitting and debug it as a block.

- [ ] 3.1 `[HAND-WRITE]` Layer 1 — skeleton with a **fake tool only**:
      define `add(a, b)` as the only tool, no bash, no Docker yet. Write
      `run_agent(task, tools, model, max_steps)`:
      - build initial `messages = [system, user(task)]`
      - loop: call `llm.py`, append response, stop if `max_steps` hit
      - no action execution yet — just confirm the loop calls the model
        repeatedly and appends correctly.
- [ ] 3.2 `[HAND-WRITE]` Layer 2 — wire in actual execution of `add`: when
      `response.tool_calls` is non-empty, call the matching Python function,
      append the result as a tool-result message. Test task: "use the add
      tool to compute 3+4, then 7+5, then tell me the final sum." Confirms
      the append/repeat mechanics work with a trivial, deterministic tool.
- [ ] 3.3 `[HAND-WRITE]` Layer 3 — termination. `[DECISION]` **special
      `submit` tool** (recommended, most robust) vs. magic string vs.
      implicit "stopped calling tools." Implement `response.declares_done()`
      checking for a `submit` tool call specifically.
- [ ] 3.4 `[HAND-WRITE]` Layer 4 — the "model just talked, no action" branch:
      if no tool call and no submit, append a nudge message ("Reply with an
      action or call submit.") rather than crashing or silently looping.
      Test by prompting in a way likely to make the model just chat.
- [ ] 3.5 `[HAND-WRITE]` Layer 5 — limits: `max_steps` loop bound (already
      there from 3.1), plus `max_cost` check using the `cost_usd` running
      total from N2's `LLMResponse`. Both exit paths must **return the full
      message trace**, not just a boolean — failed runs are your future
      failure-taxonomy data (D9/D11).
- [ ] 3.6 `[HAND-WRITE]` Layer 6 — malformed-action handling: if the model
      calls a tool name not in your registry, or with args that don't match
      the schema, catch it and append an error observation ("Error: unknown
      tool 'bassh'. Available: add, submit.") instead of crashing. Add a
      consecutive-malformed-action counter; abort with a distinct
      termination reason after ~3 in a row.
- [ ] 3.7 `[HAND-WRITE]` Layer 7 — define an explicit termination-reason
      enum now (`done`, `max_steps`, `max_cost`, `too_many_errors`) even
      though tracing (N5) isn't built yet — you'll thread this value through
      later, easier to have the type ready.
- [ ] 3.8 Test — swap the fake `add` tool for a real, unsandboxed `bash`
      tool (plain `subprocess.run`, cwd = a tempdir, **not yet Docker**).
      Task: "create a file containing the first 10 primes." This is the
      exact exercise called out in §4/§11 M1. Confirms the loop works with
      a tool that has real side effects and multi-line/error-prone output.
- [ ] 3.9 Deliberately test failure paths you built: give it a task that
      needs >max_steps, give it a fake tool name in the system prompt to
      bait a malformed call, give it a task where a bash command hangs
      (confirms you *don't yet* have a timeout — that's N5, note the gap).

**Done when:** the loop solves "write 10 primes to a file" via unsandboxed
bash, and you can point to the exact lines handling each of: termination,
step limit, cost limit, malformed action, and "model just talked."
Matches §11 M1's second and third bullets.

---

## Phase N4 — Tool Layer (`harness/tools.py`)

*Goal: formalize the ad-hoc `bash` call from N3.8 into a real registry with
schemas and a second action-encoding format. §6. `[HAND-WRITE]`.*

- [ ] 4.1 `[HAND-WRITE]` Define a `Tool` type: `name`, `description`,
      `input_schema` (JSON-schema-shaped dict), `executor: Callable`.
- [ ] 4.2 `[HAND-WRITE]` Implement the `bash` executor: `subprocess.run`
      with a timeout (~60s placeholder — real value tuned in N5), capturing
      stdout, stderr, and exit code, returning them concatenated in a
      predictable format (e.g. `STDOUT:\n...\nSTDERR:\n...\nEXIT: 0`).
- [ ] 4.3 `[HAND-WRITE]` Implement the `submit` executor: for the coding
      agent, this reads `git diff` in the workdir rather than trusting
      model-reported text, and returns it as the "answer."
- [ ] 4.4 `[HAND-WRITE]` Implement the dispatcher:
      `execute(tool_call) -> observation_str`, looking up by name in a
      `dict[str, Tool]` registry, raising your N3.6 malformed-tool path on
      miss.
- [ ] 4.5 `[HAND-WRITE]` Wire the registry's schemas into the `tools=`
      argument passed to `call_llm` (native tool-calling path).
- [ ] 4.6 `[DECISION]` + `[HAND-WRITE]` Implement the **text-protocol**
      alternative: system prompt instructs the model to emit
      ```` ```bash\n<cmd>\n``` ````, and you regex/parse it out instead of
      reading `tool_calls`. Keep this behind the *same* `execute()`
      interface as 4.4 so the loop in N3 doesn't care which mode is active.
- [ ] 4.7 `[HAND-WRITE]` Add a config flag (`protocol: "native" | "text"`)
      threaded from the top-level entrypoint down to the loop, switching
      which parsing path is used. This is ~30 lines per the plan and is
      your first real ablation axis (D5).
- [ ] 4.8 Test: run the exact same task (the 10-primes task, or a slightly
      harder one) once under `native`, once under `text`, same model, and
      diff the traces/step counts. Not a rigorous ablation yet — just a
      smoke test that both paths actually work end to end.

**Done when:** `bash` and `submit` both work through a registry+dispatcher,
and the same task can run under either native or text-protocol action
encoding via one config flag.

---

## Phase N5 — Context Management, Limits, Observability (`harness/context.py` + tracing)

*Goal: turn the N3 loop into something that survives long/noisy episodes
and produces analyzable output. §5. `context.py` itself is
`[HAND-WRITE]`; the trace *viewer* is `[AI-OK]`.*

### (a) Context-window management — implement in this order, each is a measurable ablation later

- [ ] 5.1 `[HAND-WRITE]` **Observation truncation**: a function
      `truncate(obs: str, max_tokens: int) -> str` that keeps head + tail
      (not just head — errors live at the end of logs) with a
      `[... N chars truncated ...]` marker in between. Use a cheap
      approximation for "tokens" (word count / 0.75, or `tiktoken` if you
      want exactness) rather than blocking on perfect counting.
- [ ] 5.2 Wire 5.1 into the loop: every observation returned from
      `execute()` passes through `truncate()` before being appended to
      `messages`. Test with a command that produces >10k chars of output
      (e.g. `find /` or a verbose test run) and confirm the message list
      stays bounded.
- [ ] 5.3 `[HAND-WRITE]` **Observation aging/masking**: keep the last K
      (e.g. 5) tool observations at full (truncated) length; replace older
      ones with a one-line stub (`"step 4: ran pytest, 3 failed"` — you can
      generate the stub from the exit code + first output line, no LLM call
      needed). Implement as a function that rewrites the `messages` list
      before each `call_llm`, not a mutation of history in place — you want
      the *stored* trace to keep full observations even if what you *send*
      is masked.
- [ ] 5.4 Test 5.3 by running a 15+ step task and confirming (via a debug
      print of message token counts) that context growth flattens after K
      steps instead of growing linearly.
- [ ] 5.5 `[DECISION, later ablation]` Compaction/summarization — **skip for
      now**, note it as a stretch/ablation for after N9's core grid is done
      (plan explicitly calls this a branch that adds a failure mode; don't
      let it block the spine).

### (b) Limits & failure handling

- [ ] 5.6 `[HAND-WRITE]` Move step/cost limits (already stubbed in N3.5)
      into named constants passed through a `Limits` object:
      `max_steps` (30–50), `max_cost_usd` (e.g. 0.50).
- [ ] 5.7 `[HAND-WRITE]` Add a real subprocess timeout to the `bash`
      executor from N4.2 (this was a known gap from N3.9) — e.g. 60s wall
      clock, kill the process group on timeout, return a clear "command
      timed out" observation rather than hanging the whole episode.
- [ ] 5.8 `[HAND-WRITE]` Confirm the consecutive-malformed-action cap from
      N3.6 is parameterized alongside the other limits, not hardcoded.
- [ ] 5.9 Test: craft a task/tool combo that deliberately runs a
      long-lived process (`sleep 120` or a dev server that never exits) and
      confirm 5.7 kills it instead of hanging your test suite.

### (c) Observability (traces)

- [ ] 5.10 `[HAND-WRITE]` Design the JSONL trace schema now, in writing,
      per D11: one line per **episode** or per **step** (pick step-level —
      more granular, episode summary can be derived from it). Fields:
      `episode_id, step, request_messages_summary, response_text,
      tool_call, observation, input_tokens, output_tokens, cost_usd,
      wall_time_s, termination_reason (final step only)`.
- [ ] 5.11 `[HAND-WRITE]` Implement a `TraceWriter` that appends one JSON
      line per step to `traces/{episode_id}.jsonl`, flushing after every
      write (so a crash mid-episode doesn't lose prior steps).
- [ ] 5.12 `[HAND-WRITE]` Wire the writer into the loop at the point of
      every model call and every tool execution — this is the one place
      it's tempting to skip fields "for now"; don't, D11 flags this schema
      as load-bearing for everything downstream.
- [ ] 5.13 `[AI-OK]` Build a ~40-line HTML or terminal trace viewer that
      reads one `.jsonl` file and prints/renders it step by step. Not
      required to be pretty — required to make debugging traces faster
      than reading raw JSON lines.
- [ ] 5.14 Test: rerun the 10-primes task, open the resulting trace in the
      viewer, confirm every step, cost figure, and the final termination
      reason are all present and correct.

**Done when:** an episode that overflows context doesn't crash or blow the
token budget, a hung subprocess gets killed, and every episode produces a
complete, inspectable JSONL trace. Matches §11 M2's trace/limits bullet.

---

## Phase N6 — Docker Sandbox (`harness/sandbox.py`)

*Goal: replace N3.8's raw `subprocess.run` with real isolation. §6.
`sandbox.py`'s control logic is `[HAND-WRITE]`; the Dockerfile is
`[AI-OK]`.*

- [ ] 6.1 `[AI-OK]` Write a `Dockerfile`: base image (`python:3.12-slim` or
      similar), install `git`, build-essential/gcc if repos need to compile
      anything, a non-root user if you want extra safety.
- [ ] 6.2 `[AI-OK]` `docker build` it locally, tag it (e.g.
      `harness-sandbox:v1`), confirm it starts (`docker run --rm -it
      harness-sandbox:v1 bash`).
- [ ] 6.3 `[HAND-WRITE]` Implement `start_container(workdir_host_path) ->
      container_id`: launches the image with the task's working directory
      mounted (or copied in), `--network none` by default, `--memory` and
      `--cpus` caps set.
- [ ] 6.4 `[HAND-WRITE]` Implement `run_in_container(container_id, cmd,
      timeout) -> (stdout, stderr, exit_code)` via `docker exec` (subprocess
      call to the `docker` CLI is simplest; the `docker` Python SDK is a
      viable alternative — either is fine, but write the wrapper yourself).
      `[DECISION]`: stateless `cd $WORKDIR && <cmd>` prepend (simpler,
      accept no persistent shell state) vs. a long-lived shell via
      `pexpect` (adds complexity for `cd`/env persistence). **Recommended:
      stateless prepend** — matches the plan's stated simpler alternative.
- [ ] 6.5 `[HAND-WRITE]` Implement `stop_container(container_id)`, called in
      a `finally` block so a crashed episode still cleans up — orphaned
      containers will otherwise silently eat resources across a long eval
      run.
- [ ] 6.6 `[HAND-WRITE]` Swap N4.2's `bash` executor to call
      `run_in_container` instead of local `subprocess.run`, keeping the same
      return-format contract so nothing upstream (loop, context truncation)
      needs to change.
- [ ] 6.7 `[AI-OK]` Write 3 hand-made toy bugs: small repos (a few files
      each) with a deliberately broken function and a test file that fails
      until it's fixed. Keep them tiny — these are sanity-check tasks, not
      your benchmark suite.
- [ ] 6.8 Run the full harness (loop + tools + context + sandbox) against
      all 3 toy bugs end-to-end, container spun up per task, destroyed
      after. Confirm traces are written correctly for all 3, including at
      least one where the agent's first attempt fails and it retries.
- [ ] 6.9 Deliberately kill/crash the harness process mid-episode (Ctrl+C)
      and confirm no orphaned containers are left running
      (`docker ps -a`) — if there are, your cleanup in 6.5 has a gap.

**Done when:** all 3 toy bugs solved end-to-end inside disposable
containers, with full JSONL traces, and no leaked containers after a forced
crash. This is §11 M2, complete.

---

## Phase N7 — Eval Runner (`eval/`)

*Goal: script that drives `{system × task × seed}` at scale. §8.3.
`[AI-OK]` — this is plumbing, not the hand-written core.*

- [ ] 7.1 Design the run-config shape: `{system, model, task_id, seed}` and
      the result-row shape from D9/§8.3: `{system, model, task, seed,
      resolved, steps, tokens_in, tokens_out, cost, wall_time,
      termination_reason, trace_path}`.
- [ ] 7.2 Write `eval/run.py`: given a list of configs, for each one — spin
      up the task's container, invoke the harness (or a baseline), collect
      the patch/answer, call the *official* grading script, append one JSON
      result row.
- [ ] 7.3 Implement resumability: before running a config, check if its
      result row already exists in the output file; skip if so. This alone
      saves you from re-running (and re-paying for) completed work every
      time a later config crashes the whole grid.
- [ ] 7.4 Implement parallelism (e.g. `concurrent.futures` with 4–8
      workers), mindful of provider rate limits — pair with N2.5's retry
      logic so a rate-limit hit doesn't kill a worker.
- [ ] 7.5 Test the runner end-to-end on exactly 1 config (1 system, 1 task,
      1 seed) before scaling up — confirms the plumbing (container
      lifecycle, grading call, result-row write) all actually connects.

**Done when:** `eval/run.py` can take a config list of size 1 and produce
one correct, schema-complete result row.

---

## Phase N7.5 — SWE-bench Setup (prerequisite for the real grid)

*§8.1. ⏱ re-check current SWE-bench tooling docs before this step —
flagged as dated-instinct-risk in the plan.*

- [ ] 7.6 `[AI-OK]` Pick 30–50 instances from SWE-bench Lite (or Verified)
      as your fixed subset; write the instance ID list to a config file so
      it's reproducible.
- [ ] 7.7 `[AI-OK]` Pull/build the **official per-task Docker images** for
      those instances — do not build your own images for this suite, the
      official ones pin exact repo commit + deps.
- [ ] 7.8 Adapt N6's `sandbox.py` to accept "use this pre-built SWE-bench
      image" instead of your own `harness-sandbox` image for these runs.
- [ ] 7.9 Get your harness completing **5 real instances**, any score — the
      goal here is plumbing correctness (image → agent → patch → official
      grading script → pass/fail), not a good number yet.
- [ ] 7.10 `[AI-OK]` Wire the *official* grading script into `eval/run.py`'s
      grading step from 7.2 — never hand-roll test-result parsing for
      SWE-bench, the edge cases are exactly why published numbers are
      comparable.

**Done when:** 5 real SWE-bench instances run through your harness end to
end and are graded by the official script. Matches §11 M3.

---

## Phase N7.75 — Comparison Systems (Baselines)

*§7. All `[AI-OK]` — pinning/wiring other people's code, not writing your
core.*

- [ ] 7.11 Write the bare-model baseline: one API call containing issue
      text + relevant file contents, asking for a unified diff, apply it,
      grade with the same official script. No loop, no tools.
- [ ] 7.12 Pin an exact `mini-swe-agent` commit (record it in
      `baselines/README.md`), wire it into `eval/run.py` as a second
      `system` value.
- [ ] 7.13 *(recommended, not mandatory)* Pin and wire `smolagents` as a
      third `system` value — gives you the tool-calling-loop vs.
      code-as-action contrast.
- [ ] 7.14 Confirm the **model string is identical** across all systems for
      a given grid cell — re-check your config generation code, this is the
      one methodology point the plan calls non-negotiable.

**Done when:** `eval/run.py` can run the same task through bare-model,
mini-swe-agent, your harness, and (optionally) smolagents, all pinned to
the same model.

---

## Phase N8 — Statistically Defensible Eval

*§8.4. `[AI-OK]` for the stats/plotting code itself.*

- [ ] 8.1 Run a **5-task pilot** across all systems × k=3 seeds first.
      Extrapolate total cost/time from this before committing to the full
      ~50-task grid (budget arithmetic in §8.4 — re-check current token
      prices).
- [ ] 8.2 Implement `pass@1` (mean success rate over k runs per config) and
      `pass^k` (solved in *all* k runs) calculators reading the result rows
      from N7.
- [ ] 8.3 Implement a Wilson 95% CI calculator over success counts; attach
      an interval to every reported rate.
- [ ] 8.4 Implement cost/efficiency aggregation: mean tokens and $ per
      *solved* task, and a steps-to-solve distribution (histogram is
      enough).
- [ ] 8.5 Build the failure taxonomy: read a sample of failed traces (via
      the N5.13 viewer) and manually classify each into categories (wrong
      edit / never reproduced bug / step-limit loop / context overflow /
      malformed action / crash). This is manual judgment, not automatable
      away — budget real time for it.
- [ ] 8.6 Launch the full grid (~50 tasks × systems × 3 seeds) via
      `eval/run.py`, using resumability (N7.3) so a crash partway through
      doesn't cost you the whole run.
- [ ] 8.7 Re-run 8.2–8.5 over the full-grid results.

**Done when:** you have a results table with CIs, a cost-per-solved-task
number per system, and a populated failure-taxonomy table. Matches §11 M4
+ M5.

---

## Phase N9 — Ablations, README, Report

*§9. `[AI-OK]` for writing/plotting; the *design decisions* you report on
must be ones you actually made and can explain.*

- [ ] 9.1 Pick 1–2 ablations from what's already implemented as a config
      flag: native-vs-text protocol (N4.7), context-aging on/off (N5.3), or
      a not-yet-built one (plan-then-execute) if time allows.
- [ ] 9.2 Run each ablation as its own mini-grid (same task subset, both
      config values, k≥3 seeds), compute the same stats as N8.
- [ ] 9.3 Write `README.md`: results table up top (with CIs and a
      fixed-model methodology note), then architecture, then design
      decisions including rejected branches (compress the BRANCH tables
      from llm-harness-plan_1.md into your own words, not copy-pasted).
- [ ] 9.4 Write `report.md`: methods, results w/ CIs, failure taxonomy,
      ablations, honest limitations (contamination, saturation caveats from
      §8.1).
- [ ] 9.5 *(optional, high leverage)* Turn `report.md` into a short blog
      post.

**Done when:** repo matches the End-State shape in CLAUDE.md, reviewer
priority order (1) results table, (2) failure taxonomy, (3) ablations,
(4) rejected-alternatives, (5) contamination honesty — is all satisfiable
by reading the README top to bottom.

---

## How to use this file day to day

- Work top to bottom; don't skip a numbered step even if it looks trivial —
  the granularity is the point.
- When you finish a **Phase**, go update CLAUDE.md's Status/Milestones
  section (M1–M6) — that file stays the compressed cross-session summary,
  this file stays the working checklist.
- If a step reveals a design question not covered here, check
  llm-harness-plan_1.md's BRANCH table for that node before improvising —
  the alternative and its trade-off is probably already mapped.
