import { createFalEditor } from "./falEditor.js";

/**
 * Paid API, via fal.ai. OpenAI's gpt-image-1 edit endpoint — a fourth
 * provider (OpenAI, not Google/BFL/Alibaba), commercial-OK per OpenAI's API
 * terms and fal's model page.
 * Pricing is quality- and size-tiered ($0.011–$0.25/image depending on
 * low/medium/high quality and output size), not a flat per-image fee, so
 * costUsd is left unset rather than picking one tier and mislabeling the
 * others (Principle 10 — never invent a false precision).
 */
export const gptImage1Edit = createFalEditor({
  id: "gpt-image-1-edit",
  license: "commercial-ok",
  endpoint: "fal-ai/gpt-image-1/edit-image",
});
