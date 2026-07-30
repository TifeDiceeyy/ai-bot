import "dotenv/config";
import http from "node:http";
import { readFile, mkdir, stat, unlink } from "node:fs/promises";
import path from "node:path";
import type { EditQuality, ImageEditor, PromptEngineer } from "./core/types.js";
import { EditorRegistry } from "./core/registry.js";
import { allEngineers } from "./engineers/index.js";
import { allEditors } from "./editors/index.js";

// A lookup, not a registry class (§9) — shared with src/index.ts via allEngineers.
const engineers: Record<string, PromptEngineer> = Object.fromEntries(
  allEngineers.map((engineer) => [engineer.id, engineer]),
);

const registry = new EditorRegistry();
for (const editor of allEditors) {
  registry.register(editor);
}

// The web app hides real model identity behind confidential codenames —
// "banana"/"dream" are the only editor ids that ever appear in a client
// request or response. All other editors/engineers stay registered above
// for CLI use. See roadmap.md for the reasoning.
const EDITOR_CODENAMES: Record<string, ImageEditor> = {
  banana: registry.select("nano-banana-pro"),
  dream: registry.select("seedream-5-pro"),
};

const QUALITY_TIERS: EditQuality[] = ["natural", "upscale"];

// Per-codename pricing for /api/quality-costs — real costs pulled from each
// editor's own costForQuality(), never a static/duplicated number (roadmap
// item #4's fix applied consistently here).
const WEB_QUALITY_COSTS: Record<
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

const WEB_ENGINEER_ID = "natural-passthrough";

const PORT = Number(process.env.PORT ?? 3000);
const OUTPUT_DIR = path.join(process.cwd(), "output");
const WEB_DIST_DIR = path.join(process.cwd(), "web-dist");
const MAX_BODY_BYTES = 25 * 1024 * 1024; // ~18MB raw image after base64 overhead

const MIME_TYPES: Record<string, string> = {
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".png": "image/png",
  ".jpg": "image/jpeg",
  ".jpeg": "image/jpeg",
  ".svg": "image/svg+xml",
  ".json": "application/json; charset=utf-8",
};

function sendJson(
  res: http.ServerResponse,
  status: number,
  body: unknown,
): void {
  const payload = JSON.stringify(body);
  res.writeHead(status, { "Content-Type": "application/json; charset=utf-8" });
  res.end(payload);
}

async function readJsonBody(req: http.IncomingMessage): Promise<unknown> {
  let received = 0;
  const chunks: Buffer[] = [];

  for await (const chunk of req) {
    received += chunk.length;
    if (received > MAX_BODY_BYTES) {
      throw Object.assign(new Error("Request body too large"), {
        statusCode: 413,
      });
    }
    chunks.push(chunk as Buffer);
  }

  const raw = Buffer.concat(chunks).toString("utf-8");
  if (!raw) return {};
  try {
    return JSON.parse(raw);
  } catch {
    throw Object.assign(new Error("Invalid JSON body"), { statusCode: 400 });
  }
}

async function serveStatic(
  res: http.ServerResponse,
  urlPath: string,
): Promise<void> {
  const relativePath = urlPath === "/" ? "index.html" : urlPath.slice(1);

  // Path-traversal guard: resolved path must stay inside WEB_DIST_DIR. The
  // separator check (not just startsWith) matters — otherwise a sibling
  // directory sharing a name prefix (e.g. "web-dist-evil") would pass a
  // bare startsWith(WEB_DIST_DIR) string check.
  const resolved = path.normalize(path.join(WEB_DIST_DIR, relativePath));
  if (
    resolved !== WEB_DIST_DIR &&
    !resolved.startsWith(WEB_DIST_DIR + path.sep)
  ) {
    sendJson(res, 400, { error: "Invalid path" });
    return;
  }

  try {
    const fileStat = await stat(resolved);
    if (!fileStat.isFile()) throw new Error("not a file");
    const ext = path.extname(resolved);
    const body = await readFile(resolved);
    res.writeHead(200, {
      "Content-Type": MIME_TYPES[ext] ?? "application/octet-stream",
    });
    res.end(body);
  } catch {
    res.writeHead(404, { "Content-Type": "text/plain" });
    res.end("Not found. Did you run `npm run build:web`?");
  }
}

interface EditRequestBody {
  imageBase64?: unknown;
  instruction?: unknown;
  quality?: unknown;
  editor?: unknown;
}

function parseQuality(value: unknown): EditQuality {
  if (value === "natural" || value === "upscale") return value;
  return "natural";
}

async function handleEdit(
  req: http.IncomingMessage,
  res: http.ServerResponse,
): Promise<void> {
  const body = (await readJsonBody(req)) as EditRequestBody;

  const { imageBase64, instruction } = body;
  if (typeof imageBase64 !== "string" || typeof instruction !== "string") {
    sendJson(res, 400, {
      error: "Body must include imageBase64 and instruction (both strings).",
    });
    return;
  }
  const quality = parseQuality(body.quality);

  const codename = typeof body.editor === "string" ? body.editor : undefined;
  const editor = codename ? EDITOR_CODENAMES[codename] : undefined;
  if (!editor) {
    sendJson(res, 400, {
      error: `Unknown editor. Available: ${Object.keys(EDITOR_CODENAMES).join(", ")}`,
    });
    return;
  }

  const engineer = engineers[WEB_ENGINEER_ID];
  if (!engineer) {
    throw new Error(
      `Misconfigured: engineer "${WEB_ENGINEER_ID}" not registered.`,
    );
  }

  if (!editor.isAvailable()) {
    sendJson(res, 400, {
      error: "Image editor is not available (missing FAL_KEY?).",
    });
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

    // Read the edit back into the response directly — no persistent/served
    // output directory at all, so there's nothing to guard against path
    // traversal and nothing that outlives this request. The on-disk file
    // (which embeds the real editor id in its name) is a transient
    // implementation detail of createFalEditor, deleted immediately after
    // we've read it, whether or not that succeeded.
    const pngBuffer = await readFile(result.imagePath);
    await unlink(result.imagePath).catch(() => {});

    sendJson(res, 200, {
      imageBase64: `data:image/png;base64,${pngBuffer.toString("base64")}`,
      width: result.width,
      height: result.height,
    });
  } catch (err) {
    sendJson(res, 502, { error: (err as Error).message ?? "Edit failed" });
  }
}

const server = http.createServer((req, res) => {
  const url = new URL(req.url ?? "/", `http://localhost:${PORT}`);

  (async () => {
    // No /api/editors or /api/engineers route — the web app intentionally
    // never exposes the model roster to the client (see WEB_EDITOR_ID above).
    // /api/quality-costs is fine to expose: it's per-tier pricing, not
    // model/engine identity.

    if (req.method === "GET" && url.pathname === "/api/quality-costs") {
      sendJson(res, 200, WEB_QUALITY_COSTS);
      return;
    }

    if (req.method === "POST" && url.pathname === "/api/edit") {
      await handleEdit(req, res);
      return;
    }

    if (req.method === "GET") {
      await serveStatic(res, url.pathname);
      return;
    }

    sendJson(res, 404, { error: "Not found" });
  })().catch((err) => {
    const statusCode = (err as { statusCode?: number }).statusCode ?? 500;
    sendJson(res, statusCode, {
      error: (err as Error).message ?? "Internal error",
    });
  });
});

async function main(): Promise<void> {
  await mkdir(OUTPUT_DIR, { recursive: true });
  server.listen(PORT, () => {
    console.log(`Studio AI web shell listening on http://localhost:${PORT}`);
  });
}

main();
