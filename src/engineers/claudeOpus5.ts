import { createVisionEngineer } from "./visionEngineer.js";

/**
 * Real (multimodal) engineer, Phase 4. Via fal.ai's openrouter/router/vision
 * endpoint so it reuses FAL_KEY — no new credential. A/B'd against
 * passthrough in US-002 — demonstrably reduced shape-size drift on a
 * generation-style prompt (591-611px vs 321-551px against a 318px expected
 * baseline). Kept.
 */
export const claudeOpus5 = createVisionEngineer({
  id: "claude-opus-5",
  model: "anthropic/claude-opus-5",
});
