# US-001: Walking Skeleton + Switching Proven

**Status:** ✅ Complete
**Phases covered:** 0 (Scaffold), 1 (Walking skeleton), 2 (Switching, proven)

## Story

As the project owner, I need one real image to go in, one real edited image to
come out, through a swappable-editor seam — so the core concept is proven
before anything else is built on top of it.

## Decisions resolved

- **Runtime:** Hosted API only, via fal.ai. No local GPU in this build.
- **Editors:** Two genuinely different ones behind the same `ImageEditor`
  interface — `nano-banana-pro` (Google, paid, via fal.ai) and
  `flux-2-klein-4b` (Black Forest Labs, Apache 2.0/open-source, via fal.ai).
- **Commercial/personal:** **Commercial** (decided 2026-07-29). Both editors
  already shipped (`nano-banana-pro`, `flux-2-klein-4b`) were re-verified
  against fal.ai's per-model commercial-use terms — both clear the §3a gate,
  no rework required.

## Acceptance criteria (from CLAUDE.md gates)

- [x] Phase 0: repo builds, `tsc --noEmit` clean, API key loads from `.env`,
      `.env.example` documents every key (`FAL_KEY`).
- [x] Phase 1: real input image (`test-input.png`) produces a real edited
      image on disk via `nano-banana-pro`, reproduced twice with consistent
      results.
- [x] Phase 2: same input + instruction, only the editor `id` flipped
      (`nano-banana-pro` -> `flux-2-klein-4b`), both return a correctly
      edited image. Passthrough `PromptEngineer` in place.

## What was explicitly NOT built (YAGNI, per §9)

Provider Router, Capability Registry, Mask Generator, Quality Evaluator,
Workflow Planner, auto model-selection, any real (non-passthrough)
PromptEngineer, local GPU runtime.

## Open decisions still blocking later phases

- Which model engineers the prompt for Phase 4? (must be multimodal)
- What is the desktop phase for? (local-GPU capability vs. packaging only)

## Files

- `src/core/types.ts`, `src/core/registry.ts`
- `src/editors/falClient.ts` (fal SDK plumbing: upload/subscribe/download/png)
- `src/editors/falEditor.ts` (Phase 3: `createFalEditor` factory, generalized
  from the two working adapters once they turned out identical except for
  id/license/endpoint/costUsd)
- `src/editors/nanoBananaPro.ts`, `fluxKlein4b.ts` (now thin config objects)
- `src/editors/index.ts` (barrel — `allEditors`; a third fal-hosted editor
  needs one new config file + one line here, nothing else touched)
- `src/engineers/passthrough.ts`
- `src/index.ts` (CLI entry)

## Phase 3 (Extract, don't invent) — Complete

- [x] Gate: hypothetical third fal-hosted provider touches one file
      (`editors/index.ts`) beyond its own new config file.
- [x] Re-verified both editors post-refactor: `tsc --noEmit` clean, both
      `nano-banana-pro` and `flux-2-klein-4b` re-run against the same fixture
      and visually confirmed correct (yellow square → red circle, background
      untouched) — refactor introduced no regression.
