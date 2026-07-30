import type {
  EditInput,
  EditQuality,
  EditResult,
  ImageEditor,
  License,
} from "../core/types.js";
import {
  falKeyAvailable,
  uploadImage,
  runFalEdit,
  saveAsPng,
} from "../fal/client.js";
import path from "node:path";

export interface QualityTierConfig {
  /** Extra fields merged into this endpoint's request body for this tier —
   * shape varies per endpoint (e.g. nano-banana-pro takes `resolution:
   * "1K"|"4K"`, seedream takes `image_size: {width, height}`), verified
   * against each endpoint's own schema, not assumed uniform (Principle 2). */
  params: Record<string, unknown>;
  /** Real cost per image at this tier, verified against fal's published
   * pricing for the actual params above — not inferred from output size. */
  costUsd: number;
}

export interface FalEditorConfig {
  id: string;
  license: License;
  endpoint: string;
  /**
   * Verified per-endpoint (Principle 2): most fal edit endpoints (nano-banana-pro,
   * flux-2-klein-4b, qwen-image-edit-2511, gpt-image-1/edit-image) take a plural
   * `image_urls` array, but flux-pro/kontext takes a singular `image_url` string —
   * confirmed against each endpoint's own published example, not assumed uniform.
   * Defaults to "urls" to keep existing editors unchanged.
   */
  imageInputMode?: "url" | "urls";
  /**
   * Per-editor mapping from the app's natural/upscale choice to this
   * endpoint's own resolution params and real cost. Extracted once two
   * genuinely different editors (nano-banana-pro's `resolution` string vs
   * seedream's `image_size` object) needed it — not invented ahead of that
   * (§9). Editors that don't support a quality knob omit this entirely.
   */
  quality?: Partial<Record<EditQuality, QualityTierConfig>>;
}

/**
 * Phase 3 extraction: nano-banana-pro and flux-2-klein-4b turned out to be
 * identical except for id/license/endpoint/costUsd once both were working.
 * This factory generalizes that observed shape — it is not a Provider
 * Router (§9) and covers only fal-hosted editors, since that's the only
 * pattern actually observed so far.
 */
export function createFalEditor(config: FalEditorConfig): ImageEditor {
  return {
    id: config.id,
    license: config.license,

    isAvailable(): boolean {
      return falKeyAvailable();
    },

    costForQuality(quality: EditQuality): number | undefined {
      return config.quality?.[quality]?.costUsd;
    },

    async edit(input: EditInput): Promise<EditResult> {
      const imageUrl = await uploadImage(input.image);
      const imageField =
        config.imageInputMode === "url"
          ? { image_url: imageUrl }
          : { image_urls: [imageUrl] };
      const qualityTier = input.quality ? config.quality?.[input.quality] : undefined;

      const images = await runFalEdit(config.endpoint, {
        prompt: input.instruction,
        ...imageField,
        ...(qualityTier?.params ?? {}),
      });
      const firstImage = images[0];
      if (!firstImage) {
        throw new Error(`${config.endpoint} returned no images.`);
      }

      const outPath = path.join(
        process.cwd(),
        "output",
        `${config.id}-${Date.now()}.png`,
      );
      const { width, height } = await saveAsPng(firstImage.url, outPath);

      return {
        imagePath: outPath,
        width,
        height,
        costUsd: qualityTier?.costUsd,
      };
    },
  };
}
