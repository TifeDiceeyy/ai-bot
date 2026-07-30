import { createVisionEngineer } from "./visionEngineer.js";

/**
 * Real (multimodal) engineer alternative to claudeOpus5/gpt4o, via the same
 * fal.ai openrouter/router/vision endpoint (no new credential). Alibaba's
 * Qwen3-VL-32B-Instruct, model id verified against OpenRouter's own catalog.
 * Anticipated by CLAUDE.md §6's PromptEngineer id list ("qwen-vl") but not
 * yet built — a fourth, non-Western-lab vision model to A/B against the
 * others on real images (§6) before it earns a default.
 */
export const qwenVl = createVisionEngineer({
  id: "qwen-vl",
  model: "qwen/qwen3-vl-32b-instruct",
});
