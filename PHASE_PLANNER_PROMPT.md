# Phase Planner Prompt (reusable template)

> Paste the block below into a **fresh** agent session (new context, no
> memory of prior planning conversations) each time you're ready to plan the
> next build phase. It is self-contained by design — the agent should need
> nothing from you except access to this repo.

---

## PROMPT (copy from here down)

### Fill in before sending (or leave blank)

```
CURRENT_PHASE: <e.g. "N2", or "N7.5", or blank>
NOTES:         <anything you already know deviates from BUILD_STEPS.md —
                optional>
```

If `CURRENT_PHASE` is filled in, treat it as authoritative — plan for
*that* phase, and use the audit (Step 1 below) only to sanity-check it,
not override it. If it's blank, the audit determines the phase.

Note on phase numbering: phases correspond to the original plan's N1–N9
spine, plus a "Phase 0" (repo/env setup, pre-N1) and a three-way split of
N7 into N7 (eval runner) / N7.5 (SWE-bench setup) / N7.75 (baselines) —
that split is a build-granularity convenience invented in `BUILD_STEPS.md`,
not part of the original spine in `llm-harness-plan_1.md`. If you think of
yourself as "on N7," check which of the three you actually mean.

---

You are planning — not building — the next phase of a project at
`c:\prjt\harness_cv`. Read, in this order:

1. `CLAUDE.md` — project definition, decision log (D1–D11), hard rules,
   milestone status.
2. `BUILD_STEPS.md` — a granular step checklist covering the whole project
   (N1–N9), tagged `[HAND-WRITE]` / `[AI-OK]` / `[DECISION]` per step.
3. `llm-harness-plan_1.md` — the full design-space rationale, including
   `[BRANCH]` tables (rejected/alternative approaches per node) and a
   Dated-Instinct Ledger (§12) of places the plan's priors may already be
   stale.
4. The actual repository state: what files/dirs exist under `harness/`,
   `eval/`, `baselines/`, `traces/`, `docs/`; git log if it's a repo;
   contents of any code already written.

### Step 1 — Audit real progress (do not trust checkboxes blindly)

`BUILD_STEPS.md` has checkboxes, but they may be stale, aspirational, or
never updated. For each phase (N1 → N9, in order), verify against the
actual repo whether its "Done when" criterion is *actually* satisfiable
right now — file exists, function is implemented, a described test was
actually run and would pass, etc. Produce a short **Progress Audit**:
which phases are genuinely complete, which are partially done (and
exactly what's missing), where the checked boxes disagree with reality.
If `BUILD_STEPS.md` checkboxes are wrong, correct them — but only mark a
box done when you've verified it, and say what you verified it against.

### Step 2 — Identify the single next phase

From the audit, identify the **one** phase (a single N-number, e.g. "N2")
that is next in dependency order and not yet complete. If two phases look
simultaneously incomplete or the boundary is ambiguous, stop and ask the
user which one to plan for — do not plan multiple phases at once. Planning
more than one phase per pass was already tried and explicitly rejected by
the user as a mistake; do not repeat it.

### Step 3 — Produce the phase plan (the actual deliverable)

Write a new file: `phase-plans/N<k>_PLAN.md` (create the `phase-plans/`
directory if absent; zero-pad or name consistently with prior files if any
exist). The file has two tracks. Do not merge them — a reader should be
able to follow Track A alone to finish the phase, and separately browse
Track B whenever they want to go deeper.

**Track A — Build steps.** Granular, numbered, checkbox-style steps to
actually complete this phase, in the same style as `BUILD_STEPS.md`
(small enough that each step is an hour or less; tagged `[HAND-WRITE]` /
`[AI-OK]` / `[DECISION]`; each ends with a concrete "done when" test).
Reuse and sharpen the relevant steps already in `BUILD_STEPS.md` rather
than inventing a parallel numbering scheme — cross-reference them.

**Track B — Broaden the knowledge, not just the build.** This is the part
that matters most for this prompt, so do not shortcut it, and **do not
build it by elaborating on `BUILD_STEPS.md` or `llm-harness-plan_1.md`.**
Both of those documents are themselves a compressed, curated output from
an earlier planning pass — reading them first and expanding their bullet
points produces an anchored, narrower version of the same list, not an
independent view of the field. Instead, follow this order strictly:

1. **Research independently first.** Before opening `BUILD_STEPS.md` or
   `llm-harness-plan_1.md` for this phase's section, identify the phase's
   subject matter purely from its name/file (e.g. N2 = "an LLM client") and
   build your own concept map of that topic from your own knowledge plus
   WebSearch/WebFetch — as if no prior plan existed. Do this before you've
   seen what the existing docs already chose to mention, so their framing
   can't narrow what you go looking for.
2. **Then** read the relevant sections of `BUILD_STEPS.md` and
   `llm-harness-plan_1.md` (including its `[BRANCH]` tables) for this phase.
3. **Reconcile, don't merge-by-default.** Note what your independent pass
   found that the existing docs didn't mention (add it), what the existing
   docs mention that your pass missed (add it, but mark it as
   "prior-plan-sourced" so the user knows which parts came from where), and
   anywhere the two disagree or the existing doc's claim looks dated —
   re-verify via search rather than trusting either blindly.

For this phase's subject matter, the resulting Track B should include:

- **Concept map.** Every term/mechanism involved (e.g. for an LLM-client
  phase: streaming, prompt caching, structured outputs, batching APIs,
  rate-limit semantics, idempotency keys, provider-specific quirks) —
  including ones the minimal build doesn't need. Say explicitly which are
  in-scope for the build and which are "know it exists, won't use it yet."
- **Alternative approaches**, beyond whatever `llm-harness-plan_1.md`'s
  `[BRANCH]` table already lists for this node — pull in anything the plan
  didn't cover, and go deeper on the ones it only summarized in one line.
- **Underlying theory/primary sources.** Original papers, RFCs, or specs
  behind the mechanism (e.g. ReAct for the control loop, the actual
  function-calling spec for a given provider), not just blog-level
  summaries. Use WebSearch/WebFetch to confirm these are still current —
  this field moves fast and the existing plan already flags several places
  its priors went stale within months (see its §12 Dated-Instinct Ledger);
  assume this phase has its own undiscovered instances and look for them.
- **Common failure modes and misconceptions** specific to this topic —
  what beginners get wrong, what production systems had to learn the hard
  way, what looks right but silently breaks at scale.
- **What production/frontier systems do differently** here, and why that's
  out of scope for this project's deliberately-minimal build (tie back to
  the relevant Decision Log entry in `CLAUDE.md` if one exists).
- **Terminology glossary** for this phase's topic — precise definitions,
  since imprecise terms are exactly where cheap-model-era confusion hides.
- **Further reading pointers** (docs, papers, canonical repos) the user can
  chase after the build step is done, explicitly marked optional/
  self-paced — this is for broadening understanding, not blocking
  progress.

Track B should be organized so the user can tell, at a glance, "this bit I
need for the build, this bit is enrichment I can read whenever." Do not
pad it with filler — every entry should be something a genuinely
knowledgeable practitioner in this specific area would consider part of
the map, even the parts this project deliberately won't use.

### Constraints (do not violate)

- You are producing a **plan document**, not code. Do not write
  implementations of `harness/loop.py`, `harness/llm.py`, `harness/tools.py`,
  or `harness/context.py` — per `CLAUDE.md`'s one hard rule, those are
  hand-written by the user only, AI assists everywhere else. If the phase
  under planning is one of those files, Track A's steps should read as
  precise instructions/pseudocode-level guidance ("implement a function
  with this signature that does X, handles Y edge case") — never a
  finished code block the user could paste in.
- Keep Track A scoped to exactly one phase. Resist the urge to sketch
  ahead into the next node "for context" beyond a one-line pointer.
- If you touch anything flagged `⏱ RE-CHECK` in either existing planning
  doc, actually re-check it (web search) rather than repeating the old
  plan's text verbatim, and note what you found vs. what was previously
  assumed.
- End the file with a short "Open decisions" list — anything tagged
  `[DECISION]` in Track A that the user still needs to make before or
  during the build, so it's not buried mid-document.

### Report back

After writing `phase-plans/N<k>_PLAN.md`, summarize for the user in under
200 words: which phase you planned, what the Progress Audit found
(including any checkbox corrections you made), and one sentence on the
single most interesting/non-obvious thing Track B surfaced.

---

## END PROMPT
