import type {
  EditQuality,
  ImageEditor,
  PromptEngineer,
} from "../src/core/types.js";
import { EditorRegistry } from "../src/core/registry.js";
import { allEngineers } from "../src/engineers/index.js";
import { allEditors } from "../src/editors/index.js";

// Vercel-function counterpart of src/server.ts's setup — same codename/
// pricing/engineer wiring, kept in sync by hand (same tradeoff already
// accepted between server.ts and telegramBot.ts). Not imported by
// server.ts itself since these run as separate deployment targets, not
// two callers of one process.

export const engineers: Record<string, PromptEngineer> = Object.fromEntries(
  allEngineers.map((engineer) => [engineer.id, engineer]),
);

const registry = new EditorRegistry();
for (const editor of allEditors) {
  registry.register(editor);
}

export const EDITOR_CODENAMES: Record<string, ImageEditor> = {
  banana: registry.select("nano-banana-pro"),
  dream: registry.select("seedream-5-pro"),
};

export const WEB_ENGINEER_ID = "natural-passthrough";

const QUALITY_TIERS: EditQuality[] = ["natural", "upscale"];

export const WEB_QUALITY_COSTS: Record<
  string,
  Partial<Record<EditQuality, number>>
> = Object.fromEntries(
  Object.entries(EDITOR_CODENAMES).map(([codename, editor]) => [
    codename,
    Object.fromEntries(
      QUALITY_TIERS.map((tier) => [tier, editor.costForQuality?.(tier)]).filter(
        (entry): entry is [EditQuality, number] => entry[1] !== undefined,
      ),
    ),
  ]),
);

export function parseQuality(value: unknown): EditQuality {
  if (value === "natural" || value === "upscale") return value;
  return "natural";
}
