# US-003: Web Frontend Shell

**Status:** ✅ Complete
**Phase:** Frontend (deferred per §0 until core works — now unblocked; not
part of the numbered Phase 0-5 build order, which governs core capabilities)

## Story

As the project owner, I want a web page over the working core so I can
edit images interactively instead of via CLI args, without adding any new
business logic — the page is a thin transport shell.

## Decisions resolved (this session)

- **Backend:** plain `node:http`, no Express — only ~4 routes needed.
- **Frontend:** Vite, vanilla TypeScript, build-only (no dev-server/HMR
  proxy) — upgrade only if iteration speed becomes a real friction point.
- **Image transport:** JSON body with base64 (`FileReader` client-side),
  not multipart — avoids needing a multipart parser on a bare http server.
- **Output delivery:** static-serve the existing `output/*.png` files
  `saveAsPng` already writes; no re-encoding for the response.

## Acceptance criteria

- [x] `GET /api/editors` and `GET /api/engineers` reflect `allEditors` /
      `engineers` dynamically (no hardcoded HTML list).
- [x] `POST /api/edit` produces the same result the CLI would for the same
      inputs — reuses `src/core`/`src/editors`/`src/engineers` unchanged.
- [x] `FAL_KEY` never appears in any response, script, or network request
      visible to the browser (verified: built bundle grepped, web/ source
      grepped, fal SDK's ApiError shape inspected — see review).
- [x] `src/index.ts` (CLI) is untouched and still works.
- [x] Page: upload → preview, instruction textarea, editor picker, engineer
      picker, run button, before/after images, status/error line.

## Verification (this session)

- `tsc --noEmit` clean on both `tsconfig.json` and `web/tsconfig.json`.
- `vite build` succeeds.
- Real end-to-end browser test (Chrome, not just curl): uploaded
  `test-input.png`, ran both `nano-banana-pro`+`passthrough` and
  `flux-2-klein-4b`+`claude-opus-5` combinations — both produced correct
  edits, rendered before/after, no console errors.
- Adversarial checks: unknown `editorId` -> 400; path traversal on
  `/output/` via literal `..` (deflected by URL normalization, falls
  through to static handler safely) and encoded `%2F` (caught by explicit
  guard) -> both blocked; 26MB oversized body -> 413, server stayed up.
- Independent review (`/review-implementation`) — see plan file for full
  writeup. Status: READY, no issues found.

## Explicitly out of scope

Phase 5+ capabilities (masking, quality evaluator, upscaling), auth/multi-user
concerns, dev-server HMR, Electron desktop shell.

## Files

- `src/server.ts` (new)
- `web/index.html`, `web/main.ts`, `web/style.css`, `web/vite.config.ts`,
  `web/tsconfig.json` (new)
- `package.json` (added `vite` devDependency, `build:web`/`server`/
  `typecheck:web` scripts)
- `.gitignore` (added `web-dist/`)
