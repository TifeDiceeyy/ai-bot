import type { ImageEditor } from "../core/types.js";
import { nanoBananaPro } from "./nanoBananaPro.js";
import { fluxKlein4b } from "./fluxKlein4b.js";
import { qwenImageEdit } from "./qwenImageEdit.js";
import { fluxKontextPro } from "./fluxKontextPro.js";
import { gptImage1Edit } from "./gptImage1Edit.js";
import { seedreamPro } from "./seedreamPro.js";

/**
 * Phase 3 gate: a hypothetical third fal-hosted editor requires one new
 * config file (like nanoBananaPro.ts) plus one line here — nothing else.
 * Proven again by qwenImageEdit/fluxKontextPro/gptImage1Edit: three more
 * providers, three more lines, no changes to the registry or seam (§5).
 */
export const allEditors: ImageEditor[] = [
  nanoBananaPro,
  fluxKlein4b,
  qwenImageEdit,
  fluxKontextPro,
  gptImage1Edit,
  seedreamPro,
];
