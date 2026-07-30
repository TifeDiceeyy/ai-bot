# US-002: Real PromptEngineer (Phase 4) — A/B vs Passthrough

**Status:** ✅ Complete
**Phase covered:** 4 (Prompt engineer earns its place)

## Decision resolved

- **Engineer model:** Claude Opus 5 (`anthropic/claude-opus-5`), via fal.ai's
  `openrouter/router/vision` endpoint. Reuses the existing `FAL_KEY` — no new
  credential needed. Chosen over Qwen-VL/GPT-4o for instruction-following
  precision on a rewriting task (per owner: "use the best").

## Method

Same fixture (`test-input.png`: blue background, yellow square) and same
editor (`nano-banana-pro`) throughout. The only variable: which
`PromptEngineer` processed a deliberately **generation-style** rough prompt
— `"A blue background with a red circle in the middle"` — the exact
anti-pattern §6 warns against (describes a target scene instead of naming an
edit + what to preserve).

Measured quantitatively (not eyeballed, per Principle 4) via raw pixel scan:
background RGB at a corner, and shape width along the center row. Expected
value if size/position were perfectly preserved: ~318px (2x upscale of the
original 159px square) centered at x=512.

## Results (2 runs each)

| Condition | Run | Background RGB | Shape width | Drift from expected 318px |
|---|---|---|---|---|
| Original | — | (40,90,200) | 159 (@512 canvas) | — |
| passthrough | 1 | (39,90,197) | 611 | +92% |
| passthrough | 2 | (39,90,197) | 591 | +86% |
| claude-opus-5 | 1 | (39,90,197) | 551 | +73% |
| claude-opus-5 | 2 | (39,90,199) | 321 | +1% |

## Verdict: **Keep the engineer**

- **Background fidelity:** a wash — both conditions preserved background
  color within 1-3 RGB units (rounding/compression noise), not a real
  differentiator.
- **Shape size fidelity:** passthrough was consistently, badly oversized
  across both runs (86-92% too large) — it never once got close. The
  engineered instruction was closer in both runs and nearly perfect in one
  (+1%). This is the demonstrable improvement the Phase 4 gate requires.
- **Instruction quality itself** was also qualitatively better: the engineer
  named the specific object it saw ("the yellow square") and explicitly
  stated size/position/background preservation, rather than passing through
  a scene description that invites regeneration.
- **Honest caveat:** the engineer's improvement is directional and real, not
  a guaranteed fix — `nano-banana-pro` itself doesn't perfectly respect
  explicit size-matching instructions even when told plainly (run 1 was
  still 73% oversized). The underlying model has its own limits; the
  engineer measurably helps, it doesn't eliminate every drift.

## What was NOT built

No engineer registry/router (§9 — only two engineers exist: passthrough and
this one, a plain lookup in `src/index.ts` is enough). No double-expansion
guard needed — `nano-banana-pro` and `flux-2-klein-4b` have no known
built-in prompt-expansion flag to disable.

## Files

- `src/fal/client.ts` (relocated from `src/editors/`, now shared by editors
  and engineers; added `runFalVision`)
- `src/engineers/claudeOpus5.ts`
- `src/index.ts` (engineer lookup + optional `engineerId` CLI arg)
