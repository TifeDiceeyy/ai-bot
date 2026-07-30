import { createFalEditor } from "./falEditor.js";

/**
 * Paid API, via fal.ai. ByteDance's Seedream 5.0 Pro — a fifth provider
 * (ByteDance, not Google/BFL/Alibaba/OpenAI), marketed as "grounded,
 * region-precise" editing (changes one element, keeps the rest of the
 * frame intact), with up to 10 reference images supported (not yet used —
 * we only pass one image today). Real-photo test showed the best identity
 * preservation of any editor tried so far, though pose-following was off
 * on one sample — see prompt-quality-reference.md.
 * Commercial-use rights consistent with fal's standard paid-API terms
 * (same basis as nano-banana-pro/flux-kontext-pro), not separately verified
 * beyond that.
 * Resolution control verified directly against the live API (Principle 2):
 * takes `image_size: {width, height}`, NOT the `image_size` string-enum
 * shape Seedream Lite uses — confirmed by testing both and checking actual
 * output dimensions, not assumed from docs. No params at all defaults to
 * 2048x2048 ($0.135 tier); explicit 1024x1024 lands in fal's <=1536x1536
 * tier ($0.0675).
 * Exposed to the web app under the codename "dream" — see server.ts.
 */
export const seedreamPro = createFalEditor({
  id: "seedream-5-pro",
  license: "commercial-ok",
  endpoint: "bytedance/seedream/v5/pro/edit",
  quality: {
    natural: { params: { image_size: { width: 1024, height: 1024 } }, costUsd: 0.0675 },
    upscale: { params: { image_size: { width: 2048, height: 2048 } }, costUsd: 0.135 },
  },
});
