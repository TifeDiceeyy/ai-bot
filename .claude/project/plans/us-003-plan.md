# Plan: US-003 — Web Frontend Shell

**Status:** Complete
**Story:** [US-003](../features/us-003-web-shell.md)

## 1. Metadata & Requirements Summary

- No database in this project — core is stateless (image in, image out via
  fal.ai). Sections below that assume a DB are marked N/A rather than
  padded with invented content (Principle 10).
- Goal: thin web transport shell over the existing, already-working
  `src/core` / `src/editors` / `src/engineers`. Zero new business logic.
- Hard constraint: `FAL_KEY` must never reach the browser.
- CLI (`src/index.ts`) stays untouched and working.

## 2. Technical Approach

Two new trees, nothing existing modified:

```
src/server.ts        <- plain node:http backend (new)
web/                  <- Vite frontend source (new)
  index.html
  main.ts
  style.css
  vite.config.ts
web-dist/             <- vite build output, gitignored (new)
```

`src/server.ts` imports `allEditors`, the `engineers` lookup, `passthrough`
id, and the core types — the exact same imports `src/index.ts` already
uses. It is the second consumer of those modules, proving they're already
transport-agnostic (no CLI-specific assumptions leaked into core/editors/
engineers) — a nice confirmation of the Phase 3 extraction, not a new one.

Build/run flow: `npm run build:web` (vite build -> web-dist/) then
`npm run server` (tsx src/server.ts, serves web-dist/ + API on one port).
No HMR/dev-proxy — rebuild-and-refresh, per your call in Discovery.

## 3. Database Changes

N/A — no database in this project.

## 4. API Layer

```ts
// Request/response shapes (used by both server.ts and web/main.ts —
// duplicated as plain types on each side rather than a shared package,
// since introducing a shared-types build step for ~3 endpoints would be
// more machinery than the endpoints themselves; revisit only if the API
// surface grows.)

GET  /api/editors
  -> { id: string; license: "commercial-ok" | "non-commercial"; available: boolean }[]

GET  /api/engineers
  -> { id: string }[]

POST /api/edit
  body: { imageBase64: string; instruction: string; editorId: string; engineerId: string }
  -> 200 { imagePath: string; width: number; height: number; costUsd?: number; engineerInstruction: string }
  -> 4xx { error: string }   // bad input, unknown id, editor unavailable
  -> 5xx { error: string }   // upstream fal.ai/Claude failure

GET  /output/:filename
  -> the PNG file (existing saveAsPng output), 404 if missing

GET  /*
  -> static files from web-dist/, index.html for unmatched paths
```

`imagePath` returned to the client is rewritten to a `/output/<basename>`
URL server-side — the client never sees or needs the absolute filesystem
path `saveAsPng` writes internally.

## 5. Component Architecture (frontend)

Single page, no routing, no framework — plain DOM manipulation in
`main.ts`, mirroring the structure the archived Electron `renderer.js`
already used (same UI shape, different transport):

- File input -> local preview via `URL.createObjectURL`
- Instruction `<textarea>`
- Two `<select>` elements, populated on load from `/api/editors` and
  `/api/engineers`
- Run button -> disabled while in flight
- Before/after `<img>` panes
- Status/error line

## 6. State Management

No state library. A handful of module-level `let` bindings in `main.ts`
(`currentImageBase64`, in-flight boolean for the run button). This is a
5-field form, not an app — a state library would be pure overhead.

## 7. Edge Cases & Error Handling

- No image selected / no instruction typed -> disable Run button client-side
  (mirrors existing CLI's argv validation).
- Unknown `editorId`/`engineerId` -> server returns 400 with the same
  message shape `EditorRegistry.select()` / the engineer lookup already
  throw for the CLI (reused, not reinvented).
- Editor unavailable (`isAvailable()` false, e.g. missing `FAL_KEY`) -> 400
  with a clear message, same as CLI's existing check.
- fal.ai/Claude call throws -> 502, message forwarded (already sanitized —
  these errors don't contain the key).
- Oversized image upload -> cap body size in the server's request-body
  reader (e.g. 25MB) and return 413; prevents an unbounded buffer read on
  the bare `node:http` server, which has no built-in body-size limit the
  way a framework might.
- Static file path traversal on `/output/:filename` -> reject any filename
  containing `/` or `..` before touching the filesystem.

## 8. Testing Strategy

No test framework exists yet in this project (CLI was verified by real
runs against real fal.ai calls + pixel measurement, not unit tests — see
US-001/US-002). Consistent with that established pattern and Principle 4
("reproduce known-good output"), verification here is:

- `tsc --noEmit` clean (gate, same as every prior phase).
- Manual end-to-end run: start server, open browser, upload the existing
  `test-input.png`, run against both editors, confirm images render and
  match what the CLI already produces for the same inputs.
- Adversarial pass (Principle 6): try an unknown editorId via curl, an
  oversized payload, and a `../` filename on `/output/`, confirm each is
  rejected with the intended status code, not a crash or a leaked stack
  trace containing `FAL_KEY`.

## 9. Implementation Checklist

- [ ] `src/server.ts` — http server, routing, JSON body reader with size
      cap, static file serving with path-traversal guard
- [ ] `web/index.html`, `web/main.ts`, `web/style.css`
- [ ] `web/vite.config.ts` (outDir -> `../web-dist`)
- [ ] `package.json` — add `vite` devDependency, `build:web` and `server`
      scripts
- [ ] `.gitignore` — add `web-dist/`
- [ ] Manual E2E verification against both editors (nano-banana-pro,
      flux-2-klein-4b) and both engineers (passthrough, claude-opus-5)
- [ ] Adversarial checks (bad editorId, oversized body, path traversal)
- [ ] Update US-003 status to Complete, log results

## 10. Effort Estimate & Risks

**Effort:** small — one backend file, three frontend files, one config
file, no new architectural concepts (everything routes into code that
already works).

**Risks:**
- Bare `node:http` means hand-rolling JSON body parsing, routing, and
  static serving that a framework gives for free — slightly more code in
  `server.ts` than Express would need, in exchange for zero dependencies.
  Acceptable per your explicit choice in Discovery.
- Base64 JSON transport is ~33% larger than raw multipart bytes — fine at
  the image sizes this tool targets, would need revisiting if very large
  images become common (no evidence of that need yet — YAGNI).
- No auth/rate-limiting on `POST /api/edit` — acceptable since this is a
  local single-user tool (Electron/desktop precedent already assumed
  single-user), not a multi-tenant service.

---

## Validation Results

- **Database:** N/A — no database in this project.
- **Types:** API request/response shapes reuse existing `EditInput`/
  `EditResult`/`ImageEditor`/`PromptEngineer` types from `src/core/types.ts`
  where the shapes overlap; no redefinition of core concepts, only the
  HTTP envelope around them.
- **Standards:** Strict TypeScript (§10), secrets stay server-side only,
  matches existing patterns from `src/index.ts` (same imports, same
  registry/lookup usage) rather than inventing a new structure.
- **Acceptance criteria coverage:** 5/5 from US-003 covered (dynamic
  editor/engineer lists, same-result-as-CLI, key never exposed, CLI
  untouched, full page flow).
- **File paths referenced:** `src/core/types.ts`, `src/core/registry.ts`,
  `src/editors/index.ts`, `src/engineers/passthrough.ts`,
  `src/engineers/claudeOpus5.ts`, `src/index.ts` — all verified to exist
  from prior phases.
