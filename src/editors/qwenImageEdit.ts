import { createFalEditor } from "./falEditor.js";

/**
 * Open-source editor, hosted via fal.ai. Qwen-Image-Edit-2511 (Alibaba) is
 * Apache 2.0, verified commercial-OK per §3a at integration time (fal's own
 * model page states "fully open source with commercial use support").
 * A second, genuinely different open-source option alongside flux-2-klein-4b
 * — different lab, different architecture — strengthening the switching
 * seam rather than duplicating it.
 * Billed per output megapixel (~$0.03/MP), not a flat per-image fee, so
 * costUsd is left unset rather than inventing a number that varies with the
 * requested resolution (Principle 10).
 */
export const qwenImageEdit = createFalEditor({
  id: "qwen-image-edit-2511",
  license: "commercial-ok",
  endpoint: "fal-ai/qwen-image-edit-2511",
});
