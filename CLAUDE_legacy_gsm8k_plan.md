# CLAUDE.md — Inference-Time Compute Scaling Harness

> Context file so we keep continuity across sessions. Update the Decision Log and
> Status whenever something changes. Read this first at the start of every session.

## What this project is

A portfolio project demonstrating **engineering and evaluation rigor** around
inference-time compute scaling for LLMs. We take a small **open-weight** model and:

1. Reproduce a published benchmark number (baseline first).
2. Show Best-of-N / self-consistency beats greedy under a **compute-matched** curve.
3. **Distill** the search signal back into the model (rejection-sampling fine-tune /
   DPO) so a single cheap forward pass recovers most of the Best-of-N gain — no
   judge needed at inference.
4. (Stretch) One additional arm: LLM-judge selection, DPO-vs-RFT, or 2D query matrix.

**Not novel, and we don't claim novelty.** Value = rigor: clean compute-matched
comparisons, honest error bars, documented failures.

## Audience & success

- Reviewed by a senior AI/ML engineer + a solutions architect, and by interviewers
  (resume project). Target roles: GenAI / LLM engineer / founding AI engineer.
- **Success =** a clean, compute-matched, statistically-honest demonstration that the
  harness (and then the distilled model) beats the raw model's trivial baselines on a
  verifiable benchmark — including where it fails.
- **Explicit non-goal:** beating GPT/Gemini. Never claim this. Unfair comparisons
  destroy credibility.

## Hard constraints

- **Timeline:** ~1 week, ~4–5 hrs/day. ASAP.
- **Money:** ~$20–25 total, treated as a buffer. Default to free.
- **Hardware:** Laptop = NVIDIA T550, 4GB VRAM (cockpit: fast iteration, quantized
  1.5–3B generation, no real fine-tuning). Kaggle/Colab free T4 16GB = engine
  (batched generation via vLLM, LoRA fine-tuning).

## Key decisions (Decision Log)

- **D1: Two-stage task plan — verifiable foundation, then open-ended showcase.**
  Stage 1 = **GSM8K** (Grade School Math): ground truth removes the judge as a
  confounding variable; selection is free, instant, trustworthy — this PROVES the
  method. Stage 2 = ONE open-ended benchmark (AlpacaEval / MT-Bench) with a
  *validated* LLM-judge — this SHOWCASES intent-understanding / "best response",
  the part the user actually cares about. Open-ended is where pairwise judging
  genuinely earns its keep (no majority-vote possible). Code/HumanEval = backup.
- **D2: Base model = Qwen2.5-3B-Instruct** (strong math-for-size, easy LoRA),
  Qwen2.5-1.5B as fast fallback. Must be open-weight (distillation requires it).
- **D3: Distillation via rejection-sampling FT (STaR/RFT) / DPO, NOT PPO/RL.** Same
  goal as the senior's "RL + remove the judge", but cheaper and stable. On verifiable
  tasks the reward is ground truth, not an LLM judge. **SCOPE: stretch/finale only.**
  Core project is inference-only (sample + select, no training); fine-tuning is the
  bonus that "removes the judge" if time allows. Fine-tuning is NOT required for a
  valid result.
- **D4: All-pairs tournament judging is a *tested hypothesis*, not a default.** O(N^2)
  judge calls; under compute-matching it likely loses to majority voting. We measure it.
- **D5: MLOps-lite = Weights & Biases + clean GitHub repo + (final) Gradio on HF
  Spaces.** Vercel is NOT in scope (no GPU, can't run/train models).
- **D6: Benchmark scope guard (anti-scope-creep).** IN SCOPE for week 1 = exactly TWO
  benchmarks: **GSM8K** (Stage 1, verifiable) + **ONE** open-ended (AlpacaEval *or*
  MT-Bench, Stage 2). FALLBACKS if something breaks = MATH (harder math) or HumanEval
  (code). EVERYTHING ELSE (BBH, GPQA, MMLU, MBPP, Arena-Hard, etc.) = "future work" —
  named in the README to show landscape awareness, NOT run. Rigor = 1-2 benchmarks done
  airtight (compute-matched + CIs + validated judge), never a shallow benchmark zoo.
- **D7: RL is a *kind of* fine-tuning, not its opposite.** Spectrum: SFT (imitate) <
  RFT/STaR (filter-then-SFT) < DPO (preference) < PPO/GRPO (true online RL). We use
  RFT/DPO, not PPO — same reward-driven *spirit* the senior wanted, but stable + cheap,
  and ground truth supplies the reward PPO would have to learn.

## Senior's architecture → prior-art map (for defending choices)

| His component | Real name | Our stance |
|---|---|---|
| Many responses across temperatures | Best-of-N / self-consistency | Keep (core) |
| Compare every pair, tournament tree | All-pairs LLM-judge ranking | Challenge & measure vs majority vote |
| 2D: vary query × temperature | Query/prompt ensembling | Optional tested arm |
| RL + higher model reward, then remove | RLAIF / judge distillation (STaR/RFT/DPO/BOND) | Keep goal, use RFT/DPO + ground-truth reward |
| Benchmark raw vs harness | Benchmarking | Keep, enforce compute-matching + CIs |

## Evaluation rules (non-negotiable)

- **Compute-matched:** X-axis = total tokens (generation + judge). A method wins only
  if it's above another at *equal* X. Judge calls count against budget.
- **Bootstrap 95% CI on every accuracy** (resample questions). No CI → no claim.
  Overlapping CIs = "not shown," not "better."
- **Baselines before cleverness:** greedy + majority-vote are the bars to clear.
- **Validate any LLM judge** vs ground truth (accuracy, Cohen's kappa, position/length
  bias) before trusting it.
- **Contamination caveat:** GSM8K may be in pretraining; emphasize *relative* gains.

## Phases & status

- [ ] **Phase 0 — Reproduce greedy GSM8K number** (FIRST MILESTONE; gate to proceed).
      Also measure pass@1 vs pass@k to confirm the small model has enough coverage.
- [ ] Phase 1 — Self-consistency / Best-of-N on GSM8K, sweep N in {1,2,4,8,16,32}
- [ ] Phase 2 — Accuracy-vs-compute chart with bootstrap CIs (headline artifact #1)
- [ ] Phase 3 — Open-ended showcase: ONE open-ended benchmark + LLM-judge selection,
      VALIDATE the judge vs ground truth (accuracy, Cohen's kappa, bias), compute-matched
- [ ] Phase 4 (stretch) — Distillation (RFT/STaR or DPO LoRA on Kaggle), compute-matched
      at inference ("remove the judge")
- [ ] Throughout — W&B logging, reproducible repo

**Current status:** Scoping complete. Decisions locked (D1 two-stage, D3 fine-tuning =
stretch). Next: Kaggle setup + Phase 0.

## Conventions

- **Reproducibility:** fix seeds, pin dependencies, log every run config to W&B,
  one-command reproduce script. Save raw model outputs (don't re-generate to re-score).
- **Learning rule:** coding agents may write code, but the user reads every line and
  asks about anything unclear. No black boxes.
- **Prior art to know:** self-consistency (Wang 2022), Best-of-N, verifiers/PRMs
  (Lightman 2023), Tree of Thoughts, STaR, RFT, DPO, BOND, RLAIF, DSPy.
- **Stack:** Python, HuggingFace transformers/datasets, vLLM (Kaggle gen), PEFT/LoRA,
  TRL (DPO/SFT), Weights & Biases.

## Background calibration (user)

- Python: knows syntax, uses coding agents; wants to learn as we go.
- Solid-ish: temperature/sampling. Gaps to teach when hit: self-consistency,
  verifiers/PRM, DPO, and especially **confidence intervals / significance**.
