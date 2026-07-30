import { createFalEditor } from "./falEditor.js";

/**
 * Paid API, via fal.ai. FLUX.1 Kontext [pro] (Black Forest Labs) — a third,
 * genuinely different paid provider (BFL, not Google or OpenAI) at a lower
 * price point than nano-banana-pro. The underlying [dev] weights are
 * non-commercial (per CLAUDE.md §3a), but [pro] is API-only and fal holds a
 * commercial agreement with BFL covering its output — verified on fal's own
 * model page, not assumed from the [dev] license (Principle 2).
 * $0.04/image at integration time (flat rate — no verified natural/upscale
 * tiers, so cost isn't modeled here; this editor isn't exposed via the web
 * app's quality selector, only CLI).
 * Endpoint takes a singular `image_url`, not the plural `image_urls` most
 * other fal edit endpoints use — confirmed against fal's published example,
 * hence the explicit imageInputMode override.
 */
export const fluxKontextPro = createFalEditor({
  id: "flux-kontext-pro",
  license: "commercial-ok",
  endpoint: "fal-ai/flux-pro/kontext",
  imageInputMode: "url",
});
