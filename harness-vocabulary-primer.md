# The Language of the Harness Plan — A Self-Contained Primer

**What this is.** A one-time teaching document for every term and concept the planning document (`llm-harness-plan.md`) assumes you know. It teaches the *real* vocabulary, correctly — nothing watered down — but example-first, one new idea at a time, in dependency order. Every unit follows the same shape:

> **See it** (a concrete example) → **Name it** (the correct term + precise definition) → **In the plan** (the exact sentence from the original document where it appears) → **Check** (a question + answer).

You should be able to lift any single unit out on its own. Part G re-reads the plan's spine diagram line by line using only vocabulary taught here — that's the payoff test. Part H is the tooling/sources setup for questions after this conversation. Part I is the glossary index.

---

## PART A — First: what happened when you tried to read, and what to do about it

What you described — "my brain is stuck on one word and the rest of the words are empty" — has a boring, mechanical explanation, and it is not about your ability. Reading-comprehension research has a well-known threshold: once more than roughly 2–5% of the words in a text are unknown to you, comprehension doesn't degrade gracefully — it collapses. Your brain spends its entire working memory holding the unknown word, and nothing is left to build the sentence's meaning. The plan document probably ran at 15–20% unknown terms for you. Nobody can read that. A senior engineer who'd never touched GenAI would stall on the same paragraphs.

So the fix is not "read harder" and not "simplify the document." It's: **drive the unknown-word rate below the threshold, then reread.** Concretely:

1. **Do the one hands-on exercise in Part C, Unit 7, before anything else.** You're an inductive learner — you need one concrete anchor (a real API call you made yourself) before the abstract words can stick to anything. It takes under an hour.
2. **Read this primer once, in order.** Don't memorize; just make each Check question answerable.
3. **Reread the plan with a marker pass first:** on the first pass, do *not* try to understand — only highlight words you can't define. Look each one up in Part I's index, reread that unit. *Then* do a comprehension pass, one section at a time, and after each paragraph force yourself to say its point in one sentence out loud. If you can't, that paragraph goes into NotebookLM (Part H) as a question, verbatim.
4. **Never read more than one plan section per sitting** until the vocabulary is settled. The plan is a reference, not a novel — it was always meant to be read in lifted pieces.

**The honest timeline answer you asked for.** Your gap is *not* "further back than LLM vocabulary" in the scary sense — you program daily, you know JSON and HTTP from work even if the definitions feel shaky when isolated. Your gap is the middle layer: you've never made a raw LLM API call yourself, and the entire 2023–2026 agent/eval vocabulary is new. That's a 2–3 day gap, not a 2-month one. But: **the original 6–8 week plan does not fit in 2 weeks at full scope.** What fits in 14 days, if you work evenings-plus-weekends and cut ruthlessly:

- Days 1–2: this primer + the Unit 7 and Part D micro-exercises.
- Days 3–5: build the harness core (client, loop, tools, sandbox) — plan sections §3–§6.
- Days 6–8: SWE-bench setup + eval runner on 5 pilot tasks — plan §8.
- Days 9–11: full run at reduced scope — **3 systems only** (bare model, your harness, mini-swe-agent; drop smolagents), **~20–30 tasks** (not 50), **2 seeds** (not 3), one cheap model.
- Days 12–14: stats, failure table, README/report. Skip ablations unless a day is spare.

That reduced version is still a legitimate, defensible result — the plan itself says two baselines is "already a legitimate result." What kills the 2-week version is getting stuck silently: adopt a hard rule that any blocker lasting more than half a day goes to an AI assistant or gets cut.

---

## PART B — Foundation layer (fast refreshers; you use these at work, but the plan needs the precise versions)

### Unit 1 — Terminal, shell, bash, command

**See it.** You open a black window and type:

```
$ ls
main.py  tests/
$ python main.py
Hello
```

**Name it.** The **terminal** is the text window. The **shell** is the program inside it that reads what you type and runs it; **bash** is the most common shell on Linux. Each line you type is a **command**; when it finishes, it leaves behind three things: **stdout** (normal output text), **stderr** (error output text), and an **exit code** (a number — 0 means success, anything else means failure). Programs check exit codes to know whether a command worked without reading the text.

**In the plan:** *"`bash` — Run a shell command… return stdout+stderr+exit code."* And the whole project type is called a *"coding/terminal agent"* — an AI that works by typing commands into a shell, like you just did, instead of a human doing it.

**Check.** A command prints nothing but its exit code is 1. Did it succeed? → *No. Exit code 0 is the only success; output text is irrelevant to success detection.*

### Unit 2 — JSON

**See it.**

```json
{"name": "bash", "args": {"cmd": "ls"}, "timeout": 60}
```

**Name it.** **JSON** (JavaScript Object Notation) is a text format for structured data: `{}` holds named fields, `[]` holds lists, values are strings/numbers/true/false. It matters here for one reason: it's the format programs use to talk to each other precisely — and, as you'll see in Unit 8, it's the format an AI model uses to tell your program *exactly* what action it wants to take, with no ambiguity a human sentence would have. **JSONL** ("JSON Lines") is just a file where every line is one complete JSON object — an append-friendly log format.

**In the plan:** *"log every episode as one JSONL trace."* (Both "episode" and "trace" are taught later — Units 13 and 15.)

**Check.** Why would a program prefer receiving `{"cmd": "ls"}` over the sentence "please run ls"? → *No parsing ambiguity: field names and values are exact, so code can read them without guessing.*

### Unit 3 — API, HTTP request/response, endpoint

**See it.** This is a complete, real interaction between two computers:

```
Request  (your program sends):
POST https://api.example.com/v1/weather
{"city": "Mangaluru"}

Response (their server returns):
200 OK
{"temp_c": 27, "rain": true}
```

**Name it.** An **API** (Application Programming Interface) is a service a program can use over the internet by sending structured requests and getting structured responses — a vending machine for programs: fixed slots for input, fixed shape of output. **HTTP** is the protocol (the rules of the exchange); one exchange = one **request** and one **response**. The specific URL you send to (`/v1/weather`) is an **endpoint**. The `200 OK` is a **status code** — HTTP's version of an exit code (200-family = success, 400-family = your request was wrong, 500-family = their server broke, and **429** specifically = "you're sending too fast, slow down," which matters later in Unit 14).

**In the plan:** *"An LLM API … is a stateless HTTP endpoint."* — half of that sentence is this unit; the other half is the next one.

**Check.** Your program gets status 429 from an API. Whose fault, and what's the fix? → *Yours in a harmless way: you exceeded the rate limit; wait and retry.*

### Unit 4 — Stateless

**See it.** You call the weather API twice:

```
Call 1: {"city": "Mangaluru"}   → {"temp_c": 27}
Call 2: {"city": "same as before"} → ERROR: unknown city "same as before"
```

**Name it.** A service is **stateless** when it remembers *nothing* between calls. Every request must carry everything needed to answer it. The opposite (**stateful**) would remember your previous calls. This one word is secretly the most important in the whole plan, because LLM APIs are stateless — the model has *no memory* of your previous message — and, as Unit 7 shows, every illusion of memory is created by re-sending the entire conversation history every single time. Most of "harness design" is consequences of this fact.

**In the plan:** *"Every call sends the entire conversation so far … The model remembers nothing between calls; all 'memory' is you re-sending history."*

**Check.** If the API is stateless, how does a chatbot "remember" your name from three messages ago? → *It doesn't. The app re-sends all previous messages, including the one with your name, on every call.*

### Unit 5 — Schema

**See it.**

```json
{"name": "bash",
 "description": "Run a shell command in the sandbox",
 "input_schema": {"cmd": {"type": "string", "required": true}}}
```

**Name it.** A **schema** is a formal description of what shape data must have — which fields exist, their types, which are required. It's a contract, like a paper form with labeled boxes: the form (schema) is not a filled form (data), it defines what a valid filled form looks like. Above: the schema says "to use `bash`, you must supply one field, `cmd`, and it must be text."

**In the plan:** *"send JSON schemas, receive structured calls"* and the tool table's column header *"Schema"*. You'll see in Unit 8 that giving the model schemas is literally how it learns what actions it's allowed to take.

**Check.** Data arrives as `{"cmd": 42}`. Valid against the schema above? → *No — `cmd` must be a string, 42 is a number. Schema violations are exactly what a program can detect automatically.*

---

## PART C — The LLM layer

### Unit 6 — LLM, model, inference

**See it.** You've used ChatGPT or Claude: text in, text out. Strip away the chat website and what remains is a single mathematical function:

```
f("The capital of France is") → " Paris"
```

**Name it.** An **LLM** (Large Language Model) is a program trained on enormous amounts of text to predict likely continuations of text. "**Model**" in this field means that trained artifact itself (e.g., "GPT-5-mini" and "Claude Haiku" are models). Running the model on an input to get an output is called **inference** — and casually, "**calling the model**" (because, per Unit 3, you literally send an HTTP request to it). Crucial mental shift from the chat website: the model is not an app with memory and abilities. It is a text-continuation function behind an API, and *everything else* — memory, tools, multi-step behavior — is built around it by ordinary code. That surrounding code is what the entire plan is about.

**In the plan:** *"The model is the engine; the harness is the car."*

**Check.** Does the model itself remember your last conversation? → *No (Unit 4: stateless). Any remembering is done by code around it re-sending history.*

### Unit 7 — Prompt, messages, roles, system prompt  ⭐ do the exercise

**See it.** This is (very slightly simplified) the *actual* JSON your program sends to an LLM API, and the actual shape of the answer:

```json
Request:
{
  "model": "claude-haiku-4-5",
  "system": "You are a concise assistant.",
  "messages": [
    {"role": "user",      "content": "What is 2+2?"},
    {"role": "assistant", "content": "4"},
    {"role": "user",      "content": "Times ten?"}
  ],
  "max_tokens": 100
}

Response:
{"role": "assistant", "content": "40"}
```

**Name it.** Everything you send the model is loosely called the **prompt**. Structurally it's a **messages** list, where each message has a **role**: `user` (the human side), `assistant` (the model's own previous replies — which *you* re-send, per Unit 4), and a special standing instruction called the **system prompt** ("You are a concise assistant") that frames how the model should behave for the whole conversation. Notice the model could answer "Times ten?" only because the earlier turns were included — that's statelessness made visible. **Prompt engineering** just means deliberately designing these texts (especially the system prompt) and testing variants.

**In the plan:** *"messages = [system_prompt(tools), user(task)]"* — the first line of the plan's core pseudocode is exactly the JSON above, and *"The system prompt is part of the harness and worth versioning like code."*

**The exercise (do it now — it's the anchor for everything after):** get any API key (Anthropic, OpenAI, or free-tier OpenRouter), and from a terminal send the request above with `curl` or ten lines of Python `requests` — no SDK, no library. Then add the response to the messages list yourself and send a follow-up. When you've done this once, the words "stateless," "messages," "role," and "call the model" stop being vocabulary and become things you did.

**Check.** In the request above, who originally wrote the `"assistant"` message "4"? Who is sending it now? → *The model wrote it on a previous call; your program stored it and is re-sending it now, because the API remembers nothing.*

### Unit 8 — Tool calling / function calling, tool call, tool result, observation  ⭐ the single most important unit

**See it.** Add one field to the request from Unit 7 — a list of schemas (Unit 5) describing actions the model may request — and watch what the model sends back:

```json
Request (new field):
"tools": [{"name": "bash",
           "description": "Run a shell command",
           "input_schema": {"cmd": {"type": "string"}}}],
"messages": [{"role": "user", "content": "How many .py files are in this folder?"}]

Response:
{"role": "assistant",
 "content": "I'll check the folder.",
 "tool_calls": [{"name": "bash", "args": {"cmd": "ls *.py | wc -l"}}]}
```

**Name it.** This is **tool calling** (older synonym: **function calling**). Read the response carefully, because the most common beginner misconception dies here: **the model did not run anything.** It *cannot* run anything — it's a text function (Unit 6). It emitted a JSON blob *requesting* an action. Your code must now: read that **tool call**, actually run `ls *.py | wc -l` in a shell (Unit 1), and send the output back as a new message — called the **tool result**, or in agent vocabulary the **observation** (what the model gets to "see" as the consequence of its action):

```json
messages.append({"role": "tool", "content": "3"})   ← you send this
→ model's next response: "There are 3 Python files."
```

Why this works at all: model providers specifically fine-tuned their models to emit this JSON format reliably when tools are offered. That fine-tuning is, as the plan puts it, "the entire magic."

One more word, since it lives here: when a model confidently produces something false or nonexistent — like calling a tool named `bassh` that you never offered, or citing a file that isn't in the repo — that's a **hallucination**. Not a malfunction; the expected texture of a text-prediction machine, and the reason harnesses verify instead of trust.

**In the plan:** *"the model … emits a structured JSON blob saying 'call bash with {cmd: ...}'. The API does not run anything. Your code reads that blob, executes whatever it means, and sends the result back as a new message."*

**Check.** The model responds with a tool call for a tool named `bassh` (typo). What runs on your machine? → *Nothing. Tool calls are requests; your code looks up the name, finds nothing, and (per the plan) should send back an error message as the observation so the model can correct itself.*

### Unit 9 — Token

**See it.** The sentence `"unbelievable!"` is not, to the model, one word. It's split into pieces, roughly:

```
["un", "believ", "able", "!"]   → 4 tokens
```

**Name it.** A **token** is the unit models actually read and write — a chunk of characters, usually a word-piece; rule of thumb, 1 token ≈ ¾ of an English word, so 1,000 tokens ≈ 750 words. Everything in this field is counted and priced in tokens: API bills are "$X per million **input tokens** (what you send) and $Y per million **output tokens** (what the model writes)," and output tokens cost several times more. Since (Unit 4) you re-send the whole history every call, input-token counts *grow every step* — which is why cost management appears all over the plan.

**In the plan:** *"tokens — subword chunks, ~0.75 words each … cost scales with tokens sent."*

**Check.** A conversation history is 10,000 tokens and you make 5 more calls, each adding ~500 tokens. Roughly how many input tokens does the *fifth* call send? → *~12,000+ (the whole accumulated history goes every time — it's not 500 per call).*

### Unit 10 — Context window (and context)

**See it.** Try to paste an entire 2,000-page book into one chat message. The API refuses:

```
Error 400: prompt is 610,000 tokens, exceeds model's maximum of 200,000
```

**Name it.** The **context window** is the hard maximum number of tokens a model can take in one call — input and output combined. Everything the model can consider right now must fit in it; there is no "rest of the book on disk" from the model's point of view. "**Context**" (used as a noun constantly in this field) means *whatever is currently inside that window* — the messages, the tool schemas, all of it. Two consequences the plan is built on: (1) an agent's growing history (Unit 9's check) will eventually *hit* the window, and (2) long before it hits, it gets *expensive* — hence the plan's line "'fits' ≠ 'affordable'". Managing what stays in the window is **context management** — taught concretely in Unit 16.

**In the plan:** *"the history you re-send grows every step and the model has a hard cap (context window…)"* — and the plan's §5 is titled "Context Management" and calls it "what separates 'demo' from 'harness.'"

**Check.** Why does a 1-million-token context window not make context management unnecessary? → *Cost: you pay for every token sent, every call. A bloated window is affordable to hit once and ruinous to re-send 40 times.*

### Unit 11 — Temperature, max_tokens, deterministic

**See it.** Ask the same model the same question three times:

```
temperature 1.0:  "Paris!"   "It's Paris."   "The capital is Paris, of course."
temperature 0.0:  "Paris."   "Paris."        "Paris."  (usually)
```

**Name it.** **Temperature** is a dial (0 → ~1+) controlling randomness in the model's word choices: high = varied/creative, 0 = always pick the most likely next token. A process is **deterministic** if identical input always yields identical output. Temperature 0 makes the model *nearly* deterministic — but, and the plan leans on this hard, providers do not guarantee it: tiny infrastructure-level variations mean the same call can occasionally differ. **max_tokens** is simpler: a cap on how long the *response* may be (it does not limit your input).

**In the plan:** *"temperature (0 = near-deterministic — near, not fully … which is why §9 makes you run everything multiple times)."* This one non-guarantee is the entire reason the plan's statistics section demands multiple runs of every experiment — a single run of a not-quite-deterministic system is an anecdote, not a measurement.

**Check.** You benchmark at temperature 0 and run each task once. A friend reruns and gets a different score. Whose bug? → *Nobody's — temperature 0 is not fully deterministic across providers. The fix is multiple runs and averages (Unit 22).*

### Unit 12 — Prompt caching, rate limits, retry/backoff

**See it.** Step 12 of an agent conversation re-sends steps 1–11 unchanged, plus one new message. The provider notices the unchanged prefix:

```
input tokens: 40,000 total → 38,500 "cache hit" (billed ~10% price) + 1,500 new (full price)
```

**Name it.** **Prompt caching**: providers detect that the beginning of your request is byte-identical to a recent request and re-bill that prefix at ~10% of normal price. Agents (which re-send everything every step) are the ideal customer — caching can cut an agent's bill by 5–10×. Separately: providers cap how fast you may call (**rate limit**); exceed it and you get status 429 (Unit 3). The standard, expected response in your code is **retry with exponential backoff** — wait 1s, retry; wait 2s, 4s, 8s… These aren't errors to eliminate; they're weather to dress for.

**In the plan:** *"per-provider prompt caching (re-sent unchanged prefixes are billed at ~10% — matters a lot for agents, since each step re-sends everything)"* and *"API-level retry with exponential backoff on 429/5xx."*

**Check.** Why do agents benefit from prompt caching far more than one-off chat apps? → *Every agent step re-sends the entire unchanged history; nearly all input tokens are cache hits.*

---

## PART D — The agent layer (the plan's core vocabulary)

### Unit 13 — Agent, control loop (agent loop), step, episode

**See it.** Take Unit 8's tool-calling exchange and wrap it in a `while` loop:

```python
messages = [system, user(task)]
while True:                          # ← this loop is the whole idea
    response = call_model(messages, tools)      # Unit 7/8
    messages.append(response)
    if response.says_done: break
    output = run(response.tool_call)            # your code executes it
    messages.append(tool_result(output))        # Unit 8: observation
```

Give it the task "fix the failing test in this repo" and watch: it runs `pytest`, reads the error, opens a file, edits it, reruns `pytest`, sees green, says done. Nobody scripted those steps — the model chose each next action after seeing each observation.

**Name it.** An **agent** is exactly this: a model given tools and called in a loop, so it can act over multiple steps toward a goal instead of answering once. The loop itself is the **control loop** (or **agent loop**). One iteration — one model call, one action, one observation — is a **step**. One complete attempt at one task, start to termination, is an **episode** (a **trajectory** or **rollout** means the same episode viewed as its sequence of steps). Deflating realization worth having early: the "AI agents" industry of 2026 is, at its core, this ~10-line loop plus engineering around it.

**In the plan:** *"an 'agent' is just this request in a while-loop"* and *"N3 — The control loop (the heart, ~50 lines)."*

**Check.** What's the difference between asking a chatbot "fix this bug" and giving an agent "fix this bug"? → *The chatbot answers once with text (its guess at a fix). The agent can act — run the tests, read real output, edit, verify — over many steps, because a loop feeds it tools and observations.*

### Unit 14 — Harness, scaffold(ing)

**See it.** The loop in Unit 13 is 10 lines. Now list everything a *real* version needs around it: the system prompt telling the model how to behave; the tool definitions; code that executes tools safely; a policy for shortening the growing history (Unit 10); limits so it can't run forever or spend $100; logging of everything that happened. Stack all of that around the model:

```
        ┌─────────────────────────────────────┐
        │  HARNESS (everything below)         │
        │  system prompt · tools · loop ·     │
        │  context policy · limits · logging  │
        │        ┌───────────────┐            │
        │        │     MODEL     │  ← the only "AI" part
        │        └───────────────┘            │
        └─────────────────────────────────────┘
```

**Name it.** That surrounding structure is the **harness** — synonyms: **scaffold**, **scaffolding** (as in construction scaffolding around a building: not the building, but what lets work happen on it). Claude Code, mini-swe-agent, and your project are all harnesses; they can even wrap the *same* model and get very different results — which is the plan's central empirical claim and the reason your benchmark is interesting.

**In the plan:** *"An LLM harness (also called scaffold or agent scaffold) is everything wrapped around a base language model that turns single-turn text prediction into multi-step task completion"* and *"harness choice moves benchmark scores as much as or more than model choice."*

**Check.** Two teams use the identical model; one scores 40%, the other 61% on the same tasks. What differs? → *The harness — prompts, tools, loop design, context policy. Same engine, different car.*

### Unit 15 — ReAct, reasoning, termination condition

**See it.** One step of a well-behaved agent, in the transcript:

```
Assistant: "The test expects a sorted list; the function never sorts.   ← Reason
            I'll add sorting before the return."
Tool call:  bash {"cmd": "sed -i 's/return items/return sorted(items)/' util.py"}  ← Act
Tool result: (exit 0)                                                    ← Observe
```

**Name it.** **ReAct** ("Reason + Act", from a 2022 research paper by Yao et al.) is the pattern where each step contains explicit **reasoning** (the model thinking in text about what to do) followed by one action, followed by an observation. It is *the* default agent pattern — so default that modern tool-calling APIs (Unit 8) are essentially ReAct with the formatting handled for you. A **termination condition** is the rule deciding when the loop stops: best practice is a dedicated tool the model must call (the plan's `submit`) — an unambiguous "I'm done" signal — plus safety stops (next unit) for when it never says done.

**In the plan:** *"The dominant pattern is ReAct (Reason + Act…): each step the model produces reasoning plus one action; the environment returns an observation; repeat"* and *"How does the model 'declare done'? … The special-tool approach is the most robust."*

**Check.** Why is "the model stopped calling tools" a risky termination condition? → *Weak models often just chat for a turn without acting; treating that as "done" ends episodes prematurely. An explicit `submit` tool is unambiguous.*

### Unit 16 — Limits, timeouts, and the growing-context problem (truncation, compaction)

**See it.** Real agent disasters, one per limit:

```
no step limit    → model loops: run test, fail, same edit, run test, fail… (forever, $)
no cost limit    → one episode quietly burns $40 of tokens
no timeout       → model runs `python -m http.server` — a command that never exits;
                   your program waits for output that will never come
no output cap    → model runs `cat big.log`; 400,000 tokens of log enter the
                   history and get re-sent every remaining step (Units 9–10)
```

**Name it.** The defenses, all of which the plan mandates: a **step limit** (max loop iterations per episode, e.g. 40), a **cost limit** (max $ per episode), a **timeout** on every command (kill it after N seconds), and — the start of **context management** — **truncation**: cutting each observation down to a fixed token budget before appending it, keeping the head and tail (`[... 14,213 chars truncated ...]` in the middle) because errors usually live at the *end* of logs. Its bigger sibling is **compaction** (also **summarization**): when the whole history nears a threshold, have a model write a summary of everything so far, then restart the message list as `[system, task, summary, recent steps]` — memory by paraphrase instead of transcript. Truncation is mandatory in the plan; compaction is an optional branch.

**In the plan:** *"cap every tool output at N tokens … keeping head + tail"*; *"max steps (30–50 …), max cost per episode (e.g. $0.50), max wall-clock per tool call (subprocess timeout — the agent will run a server that never exits)."*

**Check.** Why head + tail rather than just the first N tokens of a long test log? → *The failure summary and final error are printed last; head-only truncation deletes exactly the part the model needs.*

### Unit 17 — Sandbox, Docker, container, image

**See it.** Your agent, mid-episode, decides the cleanest fix is:

```
Tool call: bash {"cmd": "rm -rf /"}     ← delete everything on the machine
```

On your laptop: catastrophe. Inside a sandbox: you shrug and start a fresh one.

**Name it.** A **sandbox** is an isolated environment where code can run without touching your real machine. The standard tool is **Docker**: an **image** is a frozen snapshot of a complete miniature computer (OS + installed software + files), and a **container** is a running, disposable instance of an image — start one per task, let the agent do anything inside it, read out the result, destroy it. Two reasons the plan makes this non-optional: safety (agents type arbitrary commands, and occasionally terrible ones), and *reproducibility* — a task frozen as an image (exact repo state, exact installed dependencies) runs identically on your machine and anyone else's, which grading (Unit 20) requires.

**In the plan:** *"N6 A sandboxed execution environment (Docker per task) — both for safety (agent runs arbitrary shell commands) and for grading"* and *"Fresh container per task; destroy after grading."*

**Check.** Beyond safety, why does benchmarking specifically need containers? → *Identical starting conditions every run: same repo commit, same dependencies, no leftovers from the previous episode — otherwise scores aren't comparable or reproducible.*

### Unit 18 — Trace, logging, observability

**See it.** One line from an agent's log file (JSONL — Unit 2):

```json
{"episode":"task_017_run2","step":9,"action":{"name":"bash","args":{"cmd":"pytest"}},
 "observation":"2 failed, 14 passed","tokens_in":18240,"cost_usd":0.011,"wall_s":6.2}
```

**Name it.** A **trace** is the complete recorded transcript of an episode — every model request and response, every action, every observation, every cost number. **Logging** is writing it down as it happens; **observability** is the general property of being able to see inside a running system afterwards (there are commercial "LLM observability" platforms — Langfuse, which you know from work, is one — but a JSONL file per episode is the same idea). The plan calls the trace format "the most load-bearing schema in the project" for a concrete reason: every later activity — grading, statistics, and especially figuring out *why* episodes failed — is done by reading traces, not by watching live.

**In the plan:** *"log every episode as one JSONL trace — every request, response, action, observation, token counts, cost, wall time, termination reason"* and *"failed traces are where all your learning … comes from."*

**Check.** An episode failed and you want to know whether the model never found the bug or found it and botched the edit. Where's the answer? → *In the trace — read the step-by-step actions and observations. Without traces, failures are unexplainable.*

---

## PART E — The evaluation layer (why the plan's second half exists)

### Unit 19 — Benchmark, task suite, benchmark landscape

**See it.** You claim "my harness is good." A skeptic asks: *at what, measured how, compared to what?* The field's answer is a shared, fixed exam:

```
a benchmark =  a fixed set of tasks
             + a fixed automatic way to score attempts
             + (usually) a public leaderboard of systems' scores
```

**Name it.** A **benchmark** is exactly that standardized exam; the set of tasks inside it is a **task suite**. Because everyone runs the *same* exam, scores become comparable across systems and papers. The **benchmark landscape** just means "the current population of benchmarks and what each measures" — which ones exist, which are trusted, which are outdated — a thing that shifts every few months (Unit 24 covers how benchmarks die). The plan's names — SWE-bench, Terminal-Bench, GAIA, tau-bench — are individual benchmarks, each testing a different agent skill (fixing real code, general terminal tasks, web research, customer-service tool use, respectively).

**In the plan:** *"eval benchmarks in this space move fast"* and the plan's §8.2 table is literally a tour of the benchmark landscape.

**Check.** Why not invent all your own test tasks instead of using a benchmark? → *Nobody can compare your numbers to anything. (The plan does suggest a few original tasks — but alongside a benchmark, never instead.)*

### Unit 20 — Ground truth, grading, unit tests, SWE-bench

**See it.** One task from SWE-bench, the plan's chosen benchmark:

```
Given:   a real Python project (frozen at one moment in its history)
         + the text of a real bug report from its GitHub page
Agent:   works in the repo, produces a code change
Grading: run the project's own test suite — including tests the agent
         never saw, written by the project's humans when *they* fixed
         this bug. All pass → resolved. Otherwise → not resolved.
```

**Name it.** **Ground truth** is an objective, non-negotiable answer key. **Grading** is checking an attempt against it automatically. Here the ground truth is **unit tests** — small programs (you know these from work) that check code behaves correctly; they pass or fail with no judgment call. **SWE-bench** ("Software Engineering benchmark") packages ~thousands of such tasks from real GitHub issues; **SWE-bench Verified** is a 500-task human-checked subset, **Lite** an easier 300, and each task ships as a ready-made Docker image (Unit 17). The alternative grading style — asking another LLM to judge whether an answer is correct, an **LLM judge** — is what research-agent benchmarks partly need, and it's noisy and costs money; "unit tests as ground truth" is precisely why the plan chose a coding agent.

**In the plan:** *"success = the repo's own (held-out) unit tests pass after the agent's patch"* and *"Grading is objective and free … ground truth, no LLM judge, no ambiguity."* (A **patch**/**diff** is just the standard text format describing "which lines of which files changed" — what `git diff` prints.)

**Check.** Why are the grading tests *hidden* from the agent? → *Otherwise the agent could hard-code whatever makes those tests pass instead of actually fixing the bug — teaching to the test, literally.*

### Unit 21 — Baseline, bare model

**See it.** Your harness resolves 14 of 30 tasks. Is 14 good? Alone, unanswerable. Now add two more rows:

```
bare model (no harness, one shot):   2 / 30
mini-swe-agent (existing harness):  16 / 30
YOUR harness:                       14 / 30
```

Suddenly 14 means something: the harness idea is worth +12 tasks over no harness, and yours is within 2 of a respected reference.

**Name it.** A **baseline** is a comparison system run on the identical tasks, whose only job is to give your number meaning. The **bare model** baseline is the degenerate harness: *one single API call* — task text in, proposed patch out, no tools, no loop, no feedback — the strongest honest meaning of "the model alone." The gap between row 1 and the others is the plan's headline result: it isolates what the *harness* contributes, since the model is identical in every row (**hold the model fixed** — the plan calls comparing different models under different harnesses "measuring nothing").

**In the plan:** *"Baseline A — bare model (mandatory…) … No loop, no tools, no feedback. Expect very low scores — that gap is your headline result."*

**Check.** Why must all three rows use the same model? → *Otherwise you can't tell whether score differences come from the harness or the model. Fixing the model isolates the variable you're studying.*

### Unit 22 — Runs, seeds, pass@1, pass^k

**See it.** Unit 11 showed the model isn't fully deterministic. So you run each task 3 times per system:

```
task_017:  run1 ✓   run2 ✗   run3 ✓
```

Across 30 tasks × 3 runs: your system succeeds in 42 of 90 attempts → **pass@1 = 46.7%** (average success rate of a single attempt). Count instead only tasks solved in *all three* runs → maybe 9 of 30 → **pass^3 = 30%**.

**Name it.** One complete attempt is a **run**; a **seed** is a number fed to randomness so a run is repeatable/labelable (run1/run2/run3 = seeds 1/2/3); the whole recipe being tested (which system × which model × which settings) is a **configuration** (**config**). **pass@1 averaged over k runs** answers "how often does one attempt succeed?" — the standard headline. **pass^k** ("pass-hat-k") answers "how often does it succeed *reliably*, every single time?" — a stricter bar that a customer-service benchmark (tau-bench) popularized, because a system that works 2 times in 3 is impressive in a paper and unusable in production. The gap between the two numbers is itself a finding about your system's consistency.

**In the plan:** *"k runs per config (k=3 minimum; temperature 0 is not deterministic across providers). Report pass@1 averaged over k … and optionally pass^k."*

**Check.** System A: pass@1 = 50%, pass^3 = 45%. System B: pass@1 = 55%, pass^3 = 20%. Which do you deploy? → *Probably A — B succeeds slightly more often on average but is wildly inconsistent; A does what it does reliably.*

### Unit 23 — Confidence interval (and the Wilson interval)

**See it.** Flip a fair coin 10 times; you might easily get 7 heads. Conclude "70% heads coin"? Obviously not — 10 flips is too few to pin the true rate down. Benchmark tasks are the flips:

```
14/30 tasks solved  →  measured 46.7%, but the TRUE ability is only
                       pinned down to roughly 30%–64%  (95% confidence)
```

**Name it.** A **confidence interval (CI)** is the honest range around a measured percentage: "given only n observations, the true rate plausibly lies anywhere in here." The **Wilson interval** is simply the standard, well-behaved formula for computing it for pass/fail data (better than the naive formula when n is small or rates are extreme — you call a library function, `statsmodels` or similar, not derive it). The consequence with teeth: with n=30 tasks, intervals are ±13–18 points wide, so **your 46.7% vs mini-swe-agent's 53.3% likely overlap — and then you may not claim either one is better.** Writing that refusal explicitly in your report is, per the plan, exactly what separates portfolio projects that impress from ones that embarrass.

**In the plan:** *"with n=50 tasks, a Wilson 95% interval on a 40% success rate is roughly ±13 points. Print intervals on every number; refuse to claim 'A beats B' inside overlapping intervals."*

**Check.** Two systems score 40% and 44% on 30 tasks. Headline: "B beats A by 4 points"? → *No. Both intervals span roughly ±15 points and overlap almost entirely; the honest statement is "no detectable difference at this sample size."*

### Unit 24 — Ablation, contamination, saturation, failure taxonomy

**See it — ablation.** You suspect your truncation policy (Unit 16) matters. Prove it by deletion:

```
full harness:                 46.7%
same harness, truncation OFF: 31.0%   → truncation is worth ~15 points
```

**Name it.** An **ablation** (borrowed from surgery: remove a part, observe the change) is rerunning your system with exactly one component disabled or swapped, to measure that component's contribution. Ablations are the plan's favorite trick because each one converts a design choice into a number — and, in its words, they're "the difference between 'built a thing' and 'understands the thing.'"

**See it — contamination & saturation.** Two ways benchmarks rot: SWE-bench's repos (and the benchmark itself) are on the public internet, so they're inside models' training data — a model may half-remember the answers. That's **(data) contamination**. Separately, once top models all score 75–85% on a benchmark, it can no longer distinguish them — the exam is too easy for the class. That's **saturation**, and it's why OpenAI publicly retired SWE-bench Verified for frontier-model evaluation in 2026. The plan's point: neither rot hurts *your* study (contamination hits all your rows equally, so differences survive; cheap models are nowhere near saturation) — but naming both caveats in your report signals you know the field.

**See it — failure taxonomy.** Read every failed trace (Unit 18) and sort them into named buckets:

```
never located the buggy file: 6    edit broke other tests: 4
looped until step limit: 3         malformed tool calls: 2   context overflow: 1
```

**Name it.** A **failure taxonomy** — a classification of *how* things failed, not just how often. One such table, the plan argues, "signals more understanding than any success number."

**In the plan:** *"one or two ablations — context policy on/off, native-vs-text tool protocol…"*; *"Contamination: these repos … are in training data … affects all your columns equally, so deltas survive"*; *"classify every failure from traces."*

**Check.** Your harness beats the bare model by 30 points. A skeptic says "contamination!" Why is your *delta* still valid? → *Both systems used the same possibly-contaminated model on the same tasks; whatever memory-advantage exists, both rows had it. The difference between rows still measures the harness.*

---

## PART F — Ecosystem names (the proper nouns that read like alphabet soup)

### Unit 25 — Open source, repo, README, pinning a commit

Quick precision pass on words you use at work, as the plan uses them: **open source** = code publicly readable and reusable; a **repo(sitory)** = one project's versioned folder (on GitHub); the **README** = the repo's front page and, for a portfolio project, the most-read thing you'll write; **pinning a commit** = recording the exact version hash of any software you benchmarked (*"pin the exact commit you benchmarked and say so"*), because "I compared against mini-swe-agent" is unreproducible while "…at commit `a3f9c21`" is a scientific statement.

### Unit 26 — mini-swe-agent, SWE-agent, ACI, OpenHands

**mini-swe-agent**: a deliberately tiny (~100-line) open-source harness built by the same academic team that created SWE-bench, designed to be *the* standard baseline — bash as its only tool, no native tool-calling (it asks the model to write commands in plain text and parses them), yet >74% on SWE-bench Verified with strong models. It's the plan's mandatory comparison system *and* its recommended one-time reading ("read those 100 lines once, close the file, build your own"). Its big sibling **SWE-agent** pioneered the **ACI** (**agent-computer interface**) idea — that models do better with purpose-built structured tools (`open_file`, `edit`, `search`) than raw bash, the design school Claude Code belongs to. **OpenHands** (ex-OpenDevin) is the opposite pole: a feature-heavy production platform. The plan's repeated 2026 finding: with strong models, the minimal end matches or beats the heavy end — which is why your tiny harness is a *choice*, not a compromise.

### Unit 27 — smolagents, code-as-action

**smolagents**: Hugging Face's small agent framework, whose signature idea is **code-as-action**: instead of emitting one JSON tool call per step (Unit 8), the model writes a short *Python snippet* each step, and running the snippet *is* the action — tools are just functions available inside it. Composition (loops, conditionals over several tool uses) comes free; the price is having to sandbox arbitrary Python and messier errors. The plan wanted it as a third comparison column because it represents the *other paradigm* — under your 2-week clock, it's the cut the plan itself sanctions.

### Unit 28 — SDK, LiteLLM, OpenRouter

An **SDK** (software development kit) is a provider's official convenience library (`pip install anthropic`) wrapping the raw HTTP calls of Unit 7. Problem: each provider's request format differs slightly, and your benchmark wants to swap models freely. **LiteLLM** is an open-source translation layer — one function signature, 100+ providers behind it. **OpenRouter** solves it differently: one hosted API that resells all providers' models (one key, one format, small markup). The plan's pick: raw HTTP once (to learn), then LiteLLM or OpenRouter (to build).

### Unit 29 — MCP (Model Context Protocol)

Unit 8's tool calling is a *private conversation* between your code and one model API. **MCP** standardizes the layer above it: a protocol (open standard, created by Anthropic in Nov 2024, now under the Linux Foundation, adopted by every major vendor in 2026) for packaging tools as *servers* that any AI application can discover and use — write a "GitHub tools" server once, and Claude, ChatGPT, Cursor, and your harness can all connect to it. USB-C for AI tools. The plan's verdict for you: irrelevant to a self-contained two-tool harness (adds indirection, no benefit), but a résumé-relevant stretch goal — and important to keep straight that MCP *complements* function calling (it's the integration layer above it), not a rival to it.

### Unit 30 — LangGraph, multi-agent, plan-then-execute, reflection (the branch patterns)

Four alternative loop architectures the plan maps and mostly rejects, one line each now that you have the vocabulary: **LangGraph** represents the *workflow/state-machine* school — the agent's possible steps drawn as an explicit graph with retries and human-approval gates; production-grade, but it hides exactly the loop you're trying to learn. **Multi-agent** = several model loops delegating to each other (an orchestrator model routing subtasks to worker loops); fashionable, and 2026 consensus is that most projects using it bought complexity, not capability. **Plan-then-execute** = one extra model call up front producing an explicit step list the loop then follows; helps weak models, adds rigidity. **Reflection** = after a failed episode, the model critiques its own trace and retries with the critique in context; measurable gains, double cost. The last two are cheap ablations (Unit 24) if you find spare time.

---

## PART G — The payoff test: the spine diagram, line by line

This is the exact bottom-up chain from the plan that lost you, re-read with only vocabulary taught above. Read the plan's original alongside.

- **N1 Fundamentals** — Units 3–12: what one stateless HTTP call to a model actually contains (messages, roles, tokens) and how tool calling works on the wire (JSON schemas in, JSON tool calls out, *nothing executed by the API*).
- **N2 LLM client** — Unit 28: one function in your code that sends the messages list to any provider (via LiteLLM/OpenRouter) and hands back text + tool calls.
- **N3 Control loop** — Units 13, 15: the while-loop — call model, parse the tool call, execute, append the observation, repeat until `submit` or a limit. ReAct is the name of this rhythm.
- **N4 Tool layer** — Units 5, 8, 17: the two schemas (`bash`, `submit`) you offer the model, plus the dispatcher code that actually runs a requested command.
- **N5 "Production" features** — Units 16, 18: truncation of oversized observations, step/cost/time limits, and a JSONL trace of every episode.
- **N6 Sandbox** — Unit 17: one Docker container per task, so arbitrary commands are safe and every run starts identical.
- **N7 Eval runner** — Units 19–20, 22: a script looping over (system × task × seed), running episodes, grading each against SWE-bench's unit tests, appending one JSON result row.
- **N8 Statistically defensible eval** — Units 21–24: ≥2–3 runs per config, pass@1 with Wilson confidence intervals, cost per solved task, a failure taxonomy from the traces.
- **N9 End state** — Units 21, 24, 25: the public repo whose README leads with the table — bare model vs. your harness vs. mini-swe-agent (pinned commit), same model, same tasks — with intervals printed and claims sized to them.

If every line above read cleanly, you can now read the plan. If one line snagged, its unit numbers are right there — reread just those.

---

## PART H — After this conversation: your question-answering setup

### H.1 The tool — honest verdict

**NotebookLM remains the right call for your exact use case,** and I checked rather than assumed: the 2026 comparison landscape consistently frames NotebookLM as *the* reference point for "upload a fixed set of sources, ask questions, get answers grounded only in those sources with citations," free with a Google account. The alternatives that "beat" it win on things you don't need — team knowledge bases (Tana, Notion), academic citation management (Paperguide, SciSpace), meeting transcripts (TicNote), self-hosting (AnythingLLM). Its real limits (50 sources/notebook, Gemini-only, no persistent structure between chats) don't bite a one-project vocabulary notebook. Two honest runner-ups: **Claude Projects** (upload the same sources to a Project; answers arguably reason better, but it spends your paid quota — against your cost constraint) and **Perplexity Spaces** (better when you want sources *plus* live web; more hallucination-prone outside your corpus). Use NotebookLM; keep Claude for the moments NotebookLM's answer doesn't land.

### H.2 The source list (verified current; why each earns its place)

**Set 1 — load into the NotebookLM notebook** (these are the grounding corpus):

1. **Your two documents** — `llm-harness-plan.md` and this primer. The whole point: questions get answered *in the context of your actual plan*.
2. **Anthropic — "Building Effective Agents"** (anthropic.com/research/building-effective-agents, Dec 2024). The most-cited practitioner essay on agent design; it independently argues the plan's core thesis (simple loops beat frameworks) and defines workflows-vs-agents cleanly. Short, canonical, primary.
3. **Anthropic API docs — "Tool use" guide** (docs.claude.com). The primary-source version of Unit 8: real request/response JSON for tool calling. When you build, this is the page open in the other tab.
4. **mini-swe-agent — README + source** (github.com/SWE-agent/mini-swe-agent). Your baseline's own documentation; ~100 lines that *are* the compressed course. Paste the raw code file in as a source.
5. **SWE-bench website/paper intro** (swebench.com). Primary source for how tasks and grading actually work (Unit 20), including the Lite/Verified subsets.
6. **Lilian Weng — "LLM Powered Autonomous Agents"** (lilianweng.github.io, 2023). The classic survey that fixed the field's vocabulary — planning, memory, tool use. Slightly dated on specifics, unmatched as a terminology anchor; treat pre-2024 tool names in it as history.
7. **MCP docs — introduction page only** (modelcontextprotocol.io). For Unit 29-level questions; skip the spec.

**Set 2 — watch/do, don't upload** (video and courses don't ground well in NotebookLM):

8. **Andrej Karpathy — "Deep Dive into LLMs like ChatGPT"** (YouTube, ~3.5h) or the shorter **"Intro to Large Language Models"** (~1h). Universally regarded as the best free explanation of what a model *is* (Units 6, 9, 11 at real depth). Ex-OpenAI/Tesla; inductive, visual style that matches how you learn. Watch the 1-hour one during days 1–2; the deep-dive is optional weekend viewing.
9. **Hugging Face Agents Course, Unit 1 only** (huggingface.co/learn/agents-course — free, verified live, 200k+ certificates issued by mid-2026). Its Unit 1 teaches exactly this primer's Parts C–D (messages, tools, Think→Act→Observe) with runnable Colab notebooks — a second inductive pass from different authors. Skip its Units 2+ (framework tutorials for LangGraph/LlamaIndex/smolagents — the plan deliberately avoids frameworks). Exception: skim its smolagents unit for 20 minutes only if you keep that baseline.
10. **Anthropic Academy — "Building with the Claude API"** (anthropic.skilljar.com, free). Only if the Unit-7 exercise fights you; its early lessons walk the same first API call by hand.

Deliberately excluded: general programming/web courses (your gap isn't there — adding CS50 to a 2-week clock would be sabotage), LangChain/CrewAI tutorials (framework-first, opposite of the plan), and anything paywalled.

### H.3 Usage guide — including the "situational question" pattern

**Setup (10 minutes):** notebooklm.google.com → New notebook, name it `harness-project` → Add sources: upload the two markdown files (convert to PDF or Google Doc if .md upload complains), add items 2–7 by pasting their URLs ("Website" source type; for mini-swe-agent, open the raw file on GitHub and paste that URL or the text itself). One notebook, everything together — cross-source answers are the feature.

**The situational-question pattern** — this is the move that replaces coming back to me. Don't ask floating definitions ("what is an ablation?"); paste the confusing passage and anchor the question to it:

> *"Here is a paragraph from my plan document: '[paste the exact paragraph]'. Using the sources in this notebook, explain what this paragraph is telling me to do and why, step by step. Specifically, I don't understand what [term] means in this sentence."*

Variants that work well: *"Rewrite this paragraph as a concrete example with actual JSON/commands, like the primer's 'See it' sections"* · *"Which section of the primer teaches the vocabulary this paragraph uses?"* · *"The plan says X but mini-swe-agent's README seems to do Y — reconcile these."* Always check the citation markers in the answer — if a claim cites nothing, treat it as the model guessing and re-ask more narrowly.

### H.4 Order of operations (the whole program, sequenced)

1. **Day 1 morning:** Part A of this primer, then the Unit 7 hands-on exercise (raw API call). Anchor first.
2. **Day 1–2:** rest of this primer in order; Karpathy's 1-hour video somewhere in between as a break-that-isn't.
3. **Day 2:** set up the NotebookLM notebook (H.3). Then the marker-pass reread of the plan (Part A, step 3) — highlight, look up, *then* comprehend. Unresolved paragraphs → NotebookLM, verbatim.
4. **Day 2–3:** HF Agents Course Unit 1 notebooks (a second concrete pass), and read mini-swe-agent's 100 lines once, then close the file.
5. **Day 3 onward:** build, following the plan's milestone checklist §11 at the reduced scope from Part A. Vocabulary questions → NotebookLM; blockers >½ day → AI assistant or cut.

---

## PART I — Glossary / index

Every term the plan assumes, alphabetized, with the unit that teaches it. When a word stalls you mid-document, look here, reread that one unit, return.

| Term | Unit | | Term | Unit |
|---|---|---|---|---|
| ablation | 24 | | max_tokens | 11 |
| ACI (agent-computer interface) | 26 | | MCP | 29 |
| agent | 13 | | messages / roles | 7 |
| agent loop | 13 | | mini-swe-agent | 26 |
| API | 3 | | model | 6 |
| bare model | 21 | | multi-agent | 30 |
| baseline | 21 | | observability | 18 |
| bash / shell / terminal | 1 | | observation | 8 |
| benchmark (landscape) | 19 | | open source / repo / README | 25 |
| call the model | 6 | | OpenHands | 26 |
| compaction / summarization | 16 | | OpenRouter | 28 |
| confidence interval | 23 | | pass@1 / pass^k | 22 |
| config(uration) | 22 | | patch / diff | 20 |
| contamination | 24 | | pin a commit | 25 |
| container / image | 17 | | plan-then-execute | 30 |
| context / context window | 10 | | prompt / system prompt | 7 |
| context management | 10, 16 | | prompt caching | 12 |
| control loop | 13 | | prompt engineering | 7 |
| cost limit | 16 | | rate limit / 429 | 3, 12 |
| deterministic | 11 | | ReAct | 15 |
| Docker | 17 | | reasoning | 15 |
| endpoint | 3 | | reflection | 30 |
| episode / trajectory / rollout | 13 | | retry / exponential backoff | 12 |
| eval runner | Part G (N7) | | run / seed | 22 |
| exit code | 1 | | sandbox | 17 |
| failure taxonomy | 24 | | saturation | 24 |
| function calling | 8 | | scaffold(ing) | 14 |
| grading | 20 | | schema | 5 |
| ground truth | 20 | | SDK | 28 |
| GAIA / tau-bench / Terminal-Bench | 19 | | smolagents / code-as-action | 27 |
| hallucination (see Unit 8 check) | 8 | | stateless | 4 |
| harness | 14 | | status code | 3 |
| HTTP request/response | 3 | | stdout / stderr | 1 |
| inference | 6 | | step / step limit | 13, 16 |
| JSON / JSONL | 2 | | SWE-bench (Lite/Verified) | 20 |
| LangGraph / state machine | 30 | | task suite | 19 |
| LiteLLM | 28 | | temperature | 11 |
| LLM | 6 | | termination condition | 15 |
| LLM judge | 20 | | timeout | 16 |
| logging | 18 | | token (input/output) | 9 |
| — | — | | tool / tool call / tool calling | 8 |
| — | — | | trace | 18 |
| — | — | | truncation | 16 |
| — | — | | unit tests | 20 |
| — | — | | Wilson interval | 23 |
