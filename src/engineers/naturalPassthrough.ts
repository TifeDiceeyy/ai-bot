import type { EngineerInput, EngineerOutput, PromptEngineer } from "../core/types.js";
import { passthrough } from "./passthrough.js";

// Generic photorealism qualities only — nothing here should assume any
// particular scene, pose, or camera type, since this gets appended to
// whatever the user's own instruction describes (§6: it must not invent
// content beyond what's asked, only how it should be rendered).
// Tightened 2026-07-30 via the prompt-master skill (nidhinjs/prompt-master):
// same 5 constraints (unedited-photo framing, pore texture, no airbrushing,
// no added sharpness, no HDR/oversaturation), redundant restatements removed.
// Re-verified against the same test photo before replacing the prior wording
// — see .claude/project/prompt-quality-reference.md.
const REALISM_SUFFIX =
  "Photorealistic, unedited-photo look — not an AI-generated aesthetic: " +
  "visible skin pore texture, no airbrushing, no added sharpness or " +
  "clarity boost, natural (not artificially crisp) focus, no HDR glow or " +
  "oversaturated color.";

/**
 * The web app's actual default (2026-07-29): passthrough's raw instruction
 * with a fixed realism suffix appended, so every edit avoids the
 * "obviously AI-edited" over-sharpened look without the user having to
 * type that language themselves. Kept as its own named engineer rather
 * than baked into passthrough itself, so passthrough stays the true
 * unmodified baseline for any future A/B comparison (§6).
 */
export const naturalPassthrough: PromptEngineer = {
  id: "natural-passthrough",

  async engineer(input: EngineerInput): Promise<EngineerOutput> {
    const base = await passthrough.engineer(input);
    return { instruction: `${base.instruction} ${REALISM_SUFFIX}` };
  },
};
