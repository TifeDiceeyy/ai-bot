import type { PromptEngineer } from "../core/types.js";
import { passthrough } from "./passthrough.js";
import { naturalPassthrough } from "./naturalPassthrough.js";
import { claudeOpus5 } from "./claudeOpus5.js";
import { gpt4o } from "./gpt4o.js";
import { qwenVl } from "./qwenVl.js";

/**
 * Mirrors src/editors/index.ts. A third engineer needs one new file plus
 * one line here — the same shape the editors barrel already proved out.
 */
export const allEngineers: PromptEngineer[] = [
  passthrough,
  naturalPassthrough,
  claudeOpus5,
  gpt4o,
  qwenVl,
];
