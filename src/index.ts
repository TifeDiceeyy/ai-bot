import "dotenv/config";
import { readFile, mkdir } from "node:fs/promises";
import type { PromptEngineer } from "./core/types.js";
import { EditorRegistry } from "./core/registry.js";
import { passthrough } from "./engineers/passthrough.js";
import { allEngineers } from "./engineers/index.js";
import { allEditors } from "./editors/index.js";

// A lookup, not a registry class (§9) — shared with src/server.ts via allEngineers.
const engineers: Record<string, PromptEngineer> = Object.fromEntries(
  allEngineers.map((engineer) => [engineer.id, engineer])
);

const [, , imagePathArg, instructionArg, editorIdArg, engineerIdArg] = process.argv;

if (!imagePathArg || !instructionArg || !editorIdArg) {
  console.error(
    'Usage: npm run edit -- <imagePath> "<instruction>" <editorId> [engineerId]'
  );
  console.error(`Available editors: ${allEditors.map((e) => e.id).join(", ")}`);
  console.error(`Available engineers: ${Object.keys(engineers).join(", ")} (default: passthrough)`);
  process.exit(1);
}

const imagePath: string = imagePathArg;
const instruction: string = instructionArg;
const editorId: string = editorIdArg;
const engineerId: string = engineerIdArg ?? passthrough.id;

const registry = new EditorRegistry();
for (const editor of allEditors) {
  registry.register(editor);
}

async function main(): Promise<void> {
  await mkdir("output", { recursive: true });

  const editor = registry.select(editorId);
  if (!editor.isAvailable()) {
    throw new Error(`Editor "${editor.id}" is not available (missing FAL_KEY?).`);
  }

  const engineer = engineers[engineerId];
  if (!engineer) {
    throw new Error(`Unknown engineer id: ${engineerId}. Available: ${Object.keys(engineers).join(", ")}`);
  }

  const image = await readFile(imagePath);
  const engineered = await engineer.engineer({ image, userPrompt: instruction });

  console.log(
    `[${editor.id}] engineer=${engineer.id} instruction="${engineered.instruction}"`
  );

  const result = await editor.edit({ image, instruction: engineered.instruction });

  console.log(
    `Wrote ${result.imagePath} (${result.width}x${result.height})` +
      (result.costUsd !== undefined ? ` — est. $${result.costUsd}` : "")
  );
}

main().catch((err) => {
  console.error("Edit failed:", err.message ?? err);
  process.exit(1);
});
