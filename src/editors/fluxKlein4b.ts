import { createFalEditor } from "./falEditor.js";

/**
 * Open-source editor, hosted via fal.ai (no local GPU in this build — see
 * CLAUDE.md §12 runtime decision). FLUX.2 [klein] 4B is Apache 2.0, verified
 * commercial-OK per §3a at integration time. Genuinely different provider
 * and license class from nanoBananaPro, proving the switching seam (Phase 2).
 */
export const fluxKlein4b = createFalEditor({
  id: "flux-2-klein-4b",
  license: "commercial-ok",
  endpoint: "fal-ai/flux-2/klein/4b/edit",
});
