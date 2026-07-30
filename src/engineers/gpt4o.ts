import { createVisionEngineer } from "./visionEngineer.js";

/**
 * Real (multimodal) engineer alternative to claudeOpus5, via the same
 * fal.ai openrouter/router/vision endpoint (no new credential). OpenAI's
 * gpt-4o, model id verified against OpenRouter's own catalog. Anticipated
 * by CLAUDE.md §6's PromptEngineer id list ("gpt-4o") but not yet built —
 * this fills that gap so it can be A/B'd against claudeOpus5/passthrough
 * on real images before anyone leans on it.
 */
export const gpt4o = createVisionEngineer({
  id: "gpt-4o",
  model: "openai/gpt-4o",
});
