import "dotenv/config";
import type { VercelRequest, VercelResponse } from "@vercel/node";
import { readFile, unlink } from "node:fs/promises";
import {
  EDITOR_CODENAMES,
  engineers,
  WEB_ENGINEER_ID,
  parseQuality,
} from "./_lib.js";

interface EditRequestBody {
  imageBase64?: unknown;
  instruction?: unknown;
  quality?: unknown;
  editor?: unknown;
}

export default async function handler(
  req: VercelRequest,
  res: VercelResponse,
): Promise<void> {
  if (req.method !== "POST") {
    res.status(405).json({ error: "Method not allowed" });
    return;
  }

  const body = req.body as EditRequestBody;
  const { imageBase64, instruction } = body ?? {};
  if (typeof imageBase64 !== "string" || typeof instruction !== "string") {
    res.status(400).json({
      error: "Body must include imageBase64 and instruction (both strings).",
    });
    return;
  }
  const quality = parseQuality(body.quality);

  const codename = typeof body.editor === "string" ? body.editor : undefined;
  const editor = codename ? EDITOR_CODENAMES[codename] : undefined;
  if (!editor) {
    res.status(400).json({
      error: `Unknown editor. Available: ${Object.keys(EDITOR_CODENAMES).join(", ")}`,
    });
    return;
  }

  const engineer = engineers[WEB_ENGINEER_ID];
  if (!engineer) {
    res.status(500).json({
      error: `Misconfigured: engineer "${WEB_ENGINEER_ID}" not registered.`,
    });
    return;
  }

  if (!editor.isAvailable()) {
    res
      .status(400)
      .json({ error: "Image editor is not available (missing FAL_KEY?)." });
    return;
  }

  const commaIndex = imageBase64.indexOf(",");
  const rawBase64 =
    commaIndex !== -1 ? imageBase64.slice(commaIndex + 1) : imageBase64;
  const image = Buffer.from(rawBase64, "base64");

  try {
    const engineered = await engineer.engineer({
      image,
      userPrompt: instruction,
    });
    const result = await editor.edit({
      image,
      instruction: engineered.instruction,
      quality,
    });

    // Same no-persistence contract as src/server.ts: read the edit straight
    // into the response, delete the transient /tmp file immediately after
    // (falEditor.ts routes editors to /tmp on Vercel — see the VERCEL env
    // check there). Nothing survives past this single invocation.
    const pngBuffer = await readFile(result.imagePath);
    await unlink(result.imagePath).catch(() => {});

    res.status(200).json({
      imageBase64: `data:image/png;base64,${pngBuffer.toString("base64")}`,
      width: result.width,
      height: result.height,
    });
  } catch (err) {
    res.status(502).json({ error: (err as Error).message ?? "Edit failed" });
  }
}
