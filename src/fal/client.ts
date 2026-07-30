import { fal } from "@fal-ai/client";
import sharp from "sharp";
import { writeFile, mkdir } from "node:fs/promises";
import path from "node:path";
import { createHash } from "node:crypto";

let configured = false;

// A full edit run uploads the same source image twice — once for the
// vision-router engineer (claude-opus-5/gpt-4o/qwen-vl), once for the
// editor itself — since both receive the identical Buffer independently
// and neither knows the other already uploaded it. Caching by content hash
// (keyed on the Promise, so concurrent calls dedupe too) turns that into
// one network round trip instead of two. passthrough/natural-passthrough
// don't call uploadImage at all, so they're unaffected either way.
const uploadCache = new Map<string, Promise<string>>();

function ensureConfigured(): void {
  if (configured) return;
  const credentials = process.env.FAL_KEY;
  if (!credentials) {
    throw new Error(
      "FAL_KEY is not set. Copy .env.example to .env and fill it in.",
    );
  }
  fal.config({ credentials });
  configured = true;
}

export function falKeyAvailable(): boolean {
  return Boolean(process.env.FAL_KEY);
}

export async function uploadImage(image: Buffer): Promise<string> {
  const key = createHash("sha256").update(image).digest("hex");
  const cached = uploadCache.get(key);
  if (cached) return cached;

  ensureConfigured();
  const uploadPromise = (async () => {
    const blob = new Blob([new Uint8Array(image)]);
    return fal.storage.upload(blob);
  })();
  uploadCache.set(key, uploadPromise);
  try {
    return await uploadPromise;
  } catch (err) {
    uploadCache.delete(key); // don't cache a failed upload
    throw err;
  }
}

export async function runFalEdit(
  endpoint: string,
  input: Record<string, unknown>,
): Promise<{ url: string }[]> {
  ensureConfigured();
  const result = await fal.subscribe(endpoint, { input, logs: false });
  const images = (result.data as { images?: { url: string }[] })?.images;
  if (!images || images.length === 0) {
    throw new Error(`${endpoint} returned no images.`);
  }
  return images;
}

export async function runFalVision(
  endpoint: string,
  input: Record<string, unknown>,
): Promise<string> {
  ensureConfigured();
  const result = await fal.subscribe(endpoint, { input, logs: false });
  const output = (result.data as { output?: string })?.output;
  if (!output) {
    throw new Error(`${endpoint} returned no output text.`);
  }
  return output;
}

/**
 * Contract §5a: encoding is always PNG regardless of what the model returns,
 * and resolution is reported as the model's true native output — never invented.
 */
export async function saveAsPng(
  imageUrl: string,
  destPath: string,
): Promise<{ width: number; height: number }> {
  const response = await fetch(imageUrl);
  if (!response.ok) {
    throw new Error(
      `Failed to download edited image: ${response.status} ${response.statusText} (${imageUrl})`,
    );
  }
  const raw = Buffer.from(await response.arrayBuffer());
  const pngBuffer = await sharp(raw).png().toBuffer();
  const metadata = await sharp(pngBuffer).metadata();
  // Self-contained: don't assume the caller already created destPath's
  // directory (Phase 3 review — this was previously an unenforced contract).
  await mkdir(path.dirname(destPath), { recursive: true });
  await writeFile(destPath, pngBuffer);
  if (!metadata.width || !metadata.height) {
    throw new Error("Could not determine output image dimensions.");
  }
  return { width: metadata.width, height: metadata.height };
}
