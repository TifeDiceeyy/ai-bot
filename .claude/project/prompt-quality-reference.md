# Prompt Quality Reference

Living document capturing what "good" looks like for this app's edits, so
future prompt/engineer changes have a concrete bar to test against instead
of relying on memory of one conversation. Update this whenever a real test
changes the verdict on something below.

---

## Confirmed pipeline (web app default)

**Editor:** `nano-banana-pro`
**Engineer:** `natural-passthrough` (`src/engineers/naturalPassthrough.ts`)

Reached by testing all 5 editors against a real photo (identity
preservation + instruction-following + "no makeup" compliance) — see
`roadmap.md` for the full comparison table. `nano-banana-pro` was the only
one that consistently respected explicit instructions (makeup, mood,
setting) rather than drifting toward a generic/posed interpretation.

---

## The realism suffix — what it is and isn't allowed to do

`natural-passthrough` appends a fixed suffix to the user's own instruction,
strictly to counter the default "obviously AI-edited" look (over-sharpened,
airbrushed skin, HDR glow). Current version (tightened via the
`prompt-master` skill, 2026-07-30):

> Photorealistic, unedited-photo look — not an AI-generated aesthetic:
> visible skin pore texture, no airbrushing, no added sharpness or clarity
> boost, natural (not artificially crisp) focus, no HDR glow or
> oversaturated color.

**Hard rule, learned from a real mistake:** the suffix must describe
_rendering quality only_ — never scene, pose, camera type, or any other
content. The first draft said "like a real handheld mirror selfie," which
only made sense for the one photo it was written against. It got caught
immediately by testing a second, unrelated instruction ("change my red
sweater to black") — the wording would have been nonsensical there. If a
future edit to this suffix mentions anything a user could _see_ in the
photo rather than _how_ the whole image should feel/render, that's a
regression — revert it.

**Verification method for any future suffix change** (don't skip steps):

1. Test against the original reference case it was tuned on (green robe
   photo) — confirm no regression.
2. Test against at least one _unrelated_ instruction on the same source
   photo (e.g. a simple color-change edit) — confirms the suffix
   generalizes instead of being overfit to one scenario.
3. Only replace the working version after both pass. Keep the old version
   quoted in a code comment or here until the new one is confirmed.

---

## Editor comparison (from the real-photo test matrix)

Same source photo, same instruction, `passthrough` engineer throughout —
isolates the editor model as the only variable.

| Editor               | Verdict                                                                                               |
| -------------------- | ----------------------------------------------------------------------------------------------------- |
| **nano-banana-pro**  | Winner. Correct on makeup, mood, setting, identity.                                                   |
| flux-kontext-pro     | Ignored "no makeup" — visible brows/lips/liner.                                                       |
| flux-2-klein-4b      | Wrong mood entirely (posed smile, suburban living room instead of apartment entryway).                |
| qwen-image-edit-2511 | Lower output resolution (640x640 vs 1024x1024); odd prop logic (phone and mug crowded into one hand). |
| gpt-image-1-edit     | Functionally correct, not separately quality-ranked against the others yet.                           |

---

## Engineer comparison

| Engineer                | Verdict                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| ----------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **passthrough**         | Baseline — user's literal words, unmodified. Good instruction fidelity; identity drift depends entirely on the editor model's own behavior.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| **natural-passthrough** | Current web default — passthrough + the realism suffix above.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| claude-opus-5           | **Over-invention bug fixed, re-A/B'd 2026-08-15** (Python port, `python/src/studio_ai/engineers/vision_engineer.py`). Root cause was the old system prompt's "missing an implied action is as wrong as ignoring a stated one" directive, which explicitly told the model to invent unstated pose/prop/scene details — removed. Re-tested on a real photo (different subject than the original bug report) across 4 prompts spanning facial expression, selfie/background composition, facial reconstruction (single named feature), and environment construction: all 4 outputs named only elements actually visible in the photo (her real tattoos, actual top, actual jewelry, actual background) with no invented content, and each explicitly preserved identity/pose/framing per the instruction's own rules. Clearly more grounded and specific than `natural-passthrough`, which just echoes the raw prompt. **Prompt tightened further same day** to strictly itemize multi-feature facial requests (one clause per named anatomical feature — nose, eyebrows, eyes, mouth/smile, cheekbones, jawline, chin — never one lumped clause) while leaving background/environment requests as a single cohesive instruction rather than decomposed. Verified live via the Telegram bot (`@Tommy007mikBot`, temporarily swapped in as the active engineer in `bot.py`'s `choose_quality` handler) against a real multi-feature request ("change nose shape, cheekbone, smile line mouth shape and eyes shape"): the engineered instruction correctly split it into 5 separate reshape clauses (nose, cheekbones, smile lines, mouth/lips, eyes), each independently scoped, while explicitly preserving ethnicity, skin tone, hair, jewelry, wardrobe, pose, framing, background, and lighting — user confirmed the result was good. **Not yet promoted to any active default** — natural-passthrough remains the confirmed default; this is a real end-to-end validation (instruction + actual edited image) but the original US-002 quantitative pixel-drift methodology wasn't rerun. Still available in the registry (`runtime.py`, id `claude-opus-5`) for further testing before any promotion. |
| gpt-4o, qwen-vl         | Functionally verified (produce grounded, sensible instructions), never formally A/B'd against passthrough per CLAUDE.md §6's own bar. Treat as experimental.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |

---

## Identity-preservation notes (the original bug report)

- Passthrough + an editor model can still drift facial identity (nose,
  cheek, lip shape) even when the instruction is precise and correctly
  worded — this appears to be inherent editor-model behavior on
  scene-reconstruction-heavy prompts (e.g. "place me at home... taking a
  photo..." effectively asks for a mostly-new photo, not a small edit),
  not something passthrough vs. engineered text alone fixes.
- `nano-banana-pro` has been the most reliable at holding identity across
  this kind of heavy scene reconstruction, of everything tested so far.
- Multi-reference editing (identity photo + a separate style/pose
  reference image) was identified as a real, not-yet-built capability gap
  — `EditInput` only supports one image today. Flagged in case identity
  fidelity on heavy scene-reconstruction prompts becomes a recurring
  problem; per CLAUDE.md §7, only build this if a concrete need forces it.

---

**Last updated:** 2026-08-15
