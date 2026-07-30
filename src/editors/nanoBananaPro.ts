import { createFalEditor } from "./falEditor.js";

/**
 * Paid API, via fal.ai. Google's Nano Banana Pro — chosen for highest edit
 * accuracy on detailed, multi-step prompts (verified against fal's published
 * pricing at integration time: $0.15/image at up to 2K, $0.30 at 4K, per
 * Principle 2). Commercial-use rights confirmed on fal's model page (§3a).
 * Exposed to the web app under the codename "banana" — see server.ts.
 */
export const nanoBananaPro = createFalEditor({
  id: "nano-banana-pro",
  license: "commercial-ok",
  endpoint: "fal-ai/nano-banana-pro/edit",
  // Verified against fal's published input schema: resolution enum is
  // "1K" | "2K" | "4K", default "1K" (Principle 2).
  quality: {
    natural: { params: { resolution: "1K" }, costUsd: 0.15 },
    upscale: { params: { resolution: "4K" }, costUsd: 0.3 },
  },
});
