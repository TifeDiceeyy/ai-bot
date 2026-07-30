import type {
  EngineerInput,
  EngineerOutput,
  PromptEngineer,
} from "../core/types.js";
import { uploadImage, runFalVision } from "../fal/client.js";

const SYSTEM_INSTRUCTION = `You are a prompt engineer for an image-EDITING model, not an image-generation model.

The user's request may be written in any language, not just English. Understand it
accurately in whatever language it's written in, but always output the rewritten
instruction in clear English — the edit model itself is most reliably steered in
English regardless of what language the user typed their request in.

First, work out everything the request implies has changed — not just objects or wardrobe
named outright, but actions and poses implied by context. Example: "taking a photo of
myself" in a new location implies holding up a phone in a mirror-selfie stance, which
means the pose, arm position, and framing must change too, even though "phone" and "pose"
were never said explicitly. Missing an implied action is as wrong as ignoring a stated one.

Then rewrite the request into a single, precise, imperative editing instruction that:
- names every changed element you identified: pose/action, wardrobe, environment, lighting,
  grooming (hair/makeup), and props — whatever the request implies, stated or not
- always explicitly preserves identity — facial structure, ethnicity, skin tone, and every
  distinguishing mark (tattoos, scars, freckles) — regardless of how much else changes,
  unless the user explicitly says to alter one of them
- only preserves the original pose, composition, or framing when nothing in the request
  implies a different one is needed — never default to "keep the same pose" just because
  the user didn't spell out a new one
- is concise, precision over verbosity — never describe the whole scene as if generating it
  from scratch; state only what changes and what must persist

Output ONLY the rewritten instruction. No preamble, no quotes, no explanation.`;

export interface VisionEngineerConfig {
  id: string;
  /** OpenRouter model id passed to fal's openrouter/router/vision endpoint. */
  model: string;
}

/**
 * Extraction, mirroring editors/falEditor.ts: claudeOpus5, gpt4o, and qwenVl
 * turned out to be identical except for id/model once all three were wired
 * up — same endpoint, same system instruction, same shape. Covers only
 * fal's openrouter/router/vision engineers, since that's the only pattern
 * actually observed so far (not a generalized "engineer router").
 */
export function createVisionEngineer(
  config: VisionEngineerConfig,
): PromptEngineer {
  return {
    id: config.id,

    async engineer(input: EngineerInput): Promise<EngineerOutput> {
      const imageUrl = await uploadImage(input.image);
      const output = await runFalVision("openrouter/router/vision", {
        image_urls: [imageUrl],
        model: config.model,
        prompt: `${SYSTEM_INSTRUCTION}\n\nUser's request: ${input.userPrompt}`,
      });
      return { instruction: output.trim() };
    },
  };
}
