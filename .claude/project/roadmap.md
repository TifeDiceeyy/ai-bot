# Project Roadmap

## Studio AI

This document is the end-to-end plan for the app as it actually exists —
written from a full pass over every source file, not the phase docs in
isolation. See `CLAUDE.md` for the operational spec this build order comes
from; this file tracks _where the real code is_ against that spec.

---

## Vision

A headless core that takes an image + a plain-language request and returns
an edited image, via a swappable-model registry (open-source or paid API,
manual switching) — with a thin transport shell (web today, Electron only
if a real local-GPU need justifies it) on top. (CLAUDE.md §0)

---

## End-to-end data flow (as built)

```
Browser (web/main.ts)                       CLI (src/index.ts)
  file input --FileReader--> base64           argv --readFile--> Buffer
        |                                           |
        +-------------------+-----------------------+
                            v
              POST /api/edit (server.ts)  /  direct in-process call
                            |
                 engineers[engineerId].engineer({image, userPrompt})
                 -> passthrough: returns userPrompt unchanged
                 -> claude-opus-5 / gpt-4o / qwen-vl: uploadImage -> fal
                    openrouter/router/vision (model=<engineer's model>) -> instruction
                            |
                 registry.select(editorId).edit({image, instruction})
                 -> uploadImage -> fal.storage.upload
                 -> runFalEdit(endpoint, {prompt, image_url(s)}) -> fal.subscribe
                    (image_urls plural for most editors, image_url singular
                    for flux-kontext-pro — per-endpoint, via imageInputMode)
                 -> saveAsPng(url, outPath) -> fetch + sharp -> output/*.png
                            |
              server: rewrite path -> /output/<basename>, JSON response
              CLI: console.log path/dimensions/cost
                            |
              Browser: <img src="/output/...">  |  file on disk
```

Every consumer (CLI, server) imports the exact same
`src/core` / `src/editors` / `src/engineers` — nothing in that stack knows
whether it's being driven by a terminal or a browser. That's the thing
Phase 3 set out to prove and this review re-confirms still holds.

---

## Phases Overview

| Phase | Name                            | Status         | Evidence                                                                   |
| ----- | ------------------------------- | -------------- | -------------------------------------------------------------------------- |
| 0     | Scaffold                        | ✅ Complete    | `tsc --noEmit` clean, `.env`/`.env.example`, repo builds                   |
| 1     | Walking skeleton                | ✅ Complete    | US-001 — real image -> real edit, reproduced twice                         |
| 2     | Switching, proven               | ✅ Complete    | US-001 — 2nd genuinely different editor, same interface                    |
| 3     | Extract, don't invent           | ✅ Complete    | `createFalEditor` factory, generalized from the 2 working adapters         |
| 4     | Prompt engineer earns its place | ✅ Complete    | US-002 — A/B'd against passthrough, kept (measured improvement)            |
| —     | Web frontend shell              | ✅ Complete    | US-003 — thin shell, reuses core unchanged, security-reviewed              |
| 5+    | Earn everything else            | ⏸️ Not started | Blocked on a concrete need (masking/quality/upscaling) — none has surfaced |

---

## Phase 0: Scaffold — Complete

**Goal:** repo builds, typed, key loads.
**Delivered:** `package.json`, `tsconfig.json`, `.env`/`.env.example`
(`FAL_KEY`), `.gitignore`.

## Phase 1+2: Walking skeleton + switching — Complete (US-001)

**Goal:** prove one real edit works, then prove switching works.
**Delivered:** `src/core/types.ts` (the `ImageEditor`/`PromptEngineer`
contracts), `src/core/registry.ts`, `nanoBananaPro.ts` (paid),
`fluxKlein4b.ts` (open-source, Apache 2.0) — both real, both reproduced.

## Phase 3: Extract, don't invent — Complete

**Goal:** generalize only from what the two adapters actually turned out to
share.
**Delivered:** `src/editors/falEditor.ts`'s `createFalEditor()` factory —
the two editors collapsed to ~10-line config objects. Gate met: a third
fal-hosted editor needs one new file + one line in `src/editors/index.ts`.

## Phase 4: Prompt engineer earns its place — Complete (US-002)

**Goal:** add a real multimodal engineer, keep it only if it measurably
beats passthrough.
**Delivered:** `src/engineers/claudeOpus5.ts` (Claude Opus 5 via fal's
`openrouter/router/vision`, no new credential). A/B result: passthrough
was consistently 86-92% oversized on a generation-style prompt across 2
runs; the engineered version was closer both times, nearly exact once
(+1%). Kept.

## Web frontend shell — Complete (US-003)

**Goal:** a thin transport shell over the working core, once the core
works (§0/§12 deferred it exactly until this point).
**Delivered:** `src/server.ts` (plain `node:http`), `web/` (Vite, vanilla
TS). Reviewed for `FAL_KEY` leakage (none found, checked 4 ways), path
traversal, oversized bodies, CLI non-regression.

## Web app: model choice hidden from end users (2026-07-29)

Product decision, not a spec-driven phase: after comparing all 5 editors on
a real photo (identity preservation + instruction-following), `nano-banana-pro`

- `passthrough` was the consistent winner. The web app now hardcodes that
  pair (`WEB_EDITOR_ID`/`WEB_ENGINEER_ID` in `src/server.ts`) and never lets a
  client pick — the editor/engineer pickers were removed from `web/`, the
  `POST /api/edit` request body no longer accepts `editorId`/`engineerId`, and
  `GET /api/editors`/`GET /api/engineers` were removed entirely (they only
  existed to populate those pickers).

**Verified, not assumed:** the API was tested with the exact payload shape
the frontend now sends (`{imageBase64, instruction}`, no model fields) —
confirmed the server still produces the same quality result. This also
caught a real leak: `createFalEditor`'s output filename embeds the editor
id (e.g. `nano-banana-pro-<ts>.png`), which the old code exposed directly
via `/output/<basename>`. Fixed by copying to a random UUID filename before
returning the path — the on-disk dev-facing name (still useful for CLI
comparisons) and the client-facing name are now different files.

**CLI (`src/index.ts`) is unaffected** — full switching between all 5
editors and 4 engineers still works there for ongoing testing/comparison;
only the web surface is now fixed and opaque.

**Known open item:** `claude-opus-5` still has the over-invention bug found
during live testing (adds unrequested pose/prop details alongside its
identity-preservation language) — that's why `passthrough`-based engineers
were chosen as the hidden default rather than the engineered path, even
though the engineered path showed better identity fidelity in isolated
tests. Revisit if that engineer's system prompt gets tightened later.

## Web app default engineer: `natural-passthrough` (2026-07-29)

After the natural-photo test, the web app's `WEB_ENGINEER_ID` moved from
`passthrough` to a new `src/engineers/naturalPassthrough.ts`. It wraps
`passthrough` (keeps `passthrough` itself untouched as the true baseline)
and appends one fixed suffix requesting real-photo qualities — natural
skin texture, no smoothing/oversharpening, no HDR/AI-saturation look.

**Important constraint, caught on first attempt:** the suffix must never
reference a specific scene, pose, or camera type (the first draft said
"like a real handheld mirror selfie," which only made sense for the one
test photo). It only describes _rendering_ qualities, never content — the
actual edit content is entirely the user's own instruction, unmodified,
per §6. Verified this holds by testing a completely unrelated instruction
("change my red sweater to black") through the real `/api/edit` endpoint —
the sweater changed as asked, and the output still avoided the
over-sharpened AI look, confirming the suffix generalizes rather than
being overfit to the mirror-selfie case it was born from.

## Web app: two-way editor choice reintroduced under codenames, plus quality tiers (2026-07-30)

Supersedes part of the 2026-07-29 "model choice hidden" decision above: the
web app now offers a **choice between two editors**, but never by their real
identity. `src/server.ts`'s `EDITOR_CODENAMES` maps confidential codenames
`banana` → `nano-banana-pro` and `dream` → `seedream-5-pro`; `POST /api/edit`
accepts `editor: "banana" | "dream"` and rejects anything else, including the
real model ids (verified: sending `"nano-banana-pro"` directly gets
`400 Unknown editor`). `GET /api/editors` stays removed — codenames are
reachable only through the fixed picker, not an enumerable list. The engineer
stays hidden and fixed (`natural-passthrough`, unaffected by this change).

Reason for the two-way split: `seedream-5-pro` showed the best identity
preservation of any editor tried, `nano-banana-pro` the best
instruction-following (see `prompt-quality-reference.md`) — neither
dominates, so the product decision was to let the user pick a _feel_
(`web/index.html` labels them "Studio 1"/"Studio 2") without exposing which
underlying model that maps to.

This session also added **quality tiers** (`natural`/`upscale`) end-to-end:
`EditQuality` in `src/core/types.ts`, per-tier `params`/`costUsd` in
`createFalEditor`'s config (`src/editors/falEditor.ts`), and
`GET /api/quality-costs` returning real per-codename, per-tier pricing
(`{banana: {natural, upscale}, dream: {natural, upscale}}`) computed from
each editor's own `costForQuality()` — never a static duplicated number,
consistent with the fix applied to item #4 in the issues table below.
`web/main.ts` re-prices the quality dropdown whenever the editor picker
changes.

**Picked up mid-flight, not started fresh:** this work was already underway
in the repo (both new editor files and the codename plumbing existed) but
left the build broken — `server.ts` referenced `WEB_QUALITY_COSTS` before it
was ever defined (`tsc --noEmit` failed), and the frontend had no picker to
send the now-required `editor` field, so every real web request would have
400'd even once compiling. Fixed by defining `WEB_QUALITY_COSTS` from each
codename's `costForQuality()`, adding the `editorSelect` control to
`web/index.html`, and wiring `web/main.ts` to send it and re-fetch pricing
per editor.

**Verified, not assumed:** `tsc --noEmit` clean on both configs; `npm run
build:web` succeeds; live server hit with real `curl` payloads through
`/api/edit` for both `banana` and `dream` (both produced correct edits on
the yellow-square/red-circle-style fixture, background changed as
instructed, subject preserved); `/api/quality-costs` returns the new
per-codename shape; the real model id was confirmed rejected.

## Phase 5+: Earn everything else — Not started

Masking, a human-in-the-loop quality signal, best-effort 4K upscaling —
per §9, none of these get built until a concrete need forces one
specifically. None has surfaced yet. Do not pre-build.

---

## Known issues / follow-ups (from full-codebase review, 2026-07-29)

Found by re-reading every file in `src/` and `web/` fresh, plus live
adversarial testing against the running server — not just recalled from
memory. **All six fixed this session** (re-verified after each: `tsc
--noEmit` clean on both configs, rebuild, real browser + CLI regression
checks, adversarial checks re-run).

| #   | File                                             | Issue                                                                                                                                                                                                                                                                                                                    | Fix                                                                                                                                                                             |
| --- | ------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | `src/fal/client.ts` `saveAsPng`                  | `fetch(imageUrl)` result wasn't checked for `response.ok` before being piped into `sharp()` — a failed/expired fal URL produced an opaque "unsupported image format" error                                                                                                                                               | Added an explicit `response.ok` check with a clear "download failed: `<status>`" message                                                                                        |
| 2   | `src/server.ts` `serveStatic`/`serveOutput`      | Path-traversal guards used a bare `startsWith(BASE_DIR)`, missing the trailing-separator check — a sibling directory sharing a name prefix would technically pass the string check. Verified **not currently exploitable via HTTP** (Node's `URL` parser resolves `..` upstream), but the guard shouldn't depend on that | Hardened both to `resolved === BASE                                                                                                                                             |     | resolved.startsWith(BASE + path.sep)` |
| 3   | `web/main.ts` `loadOptions()`                    | `<option>` HTML built via raw template-string interpolation into `innerHTML` — not exploitable today, but a bad habit                                                                                                                                                                                                    | Switched to `replaceChildren`/`textContent`, verified in a real browser (dropdowns still render/populate correctly, no console errors)                                          |
| 4   | `src/editors/nanoBananaPro.ts`                   | `costUsd: 0.15` was a static estimate; fal bills 4K output at double rate                                                                                                                                                                                                                                                | `createFalEditor` now computes cost from the _actual_ returned width/height (`resolveCost()`), doubling the base rate above a 2K threshold, instead of trusting a static number |
| 5   | `src/index.ts` + `src/server.ts`                 | The `engineers` lookup was duplicated identically in both files                                                                                                                                                                                                                                                          | Extracted `src/engineers/index.ts` (`allEngineers`), mirroring the editors barrel; both CLI and server now build their lookup from it                                           |
| 6   | `src/editors/falEditor.ts` / `src/fal/client.ts` | `edit()`/`saveAsPng` assumed the output directory already existed — true only because both callers happened to `mkdir` first                                                                                                                                                                                             | `saveAsPng` now `mkdir`s its own destination directory, making it self-contained regardless of caller setup                                                                     |

---

## Editor/engineer roster expanded this session

Beyond the fixes above, the roster grew well past what US-001/US-002
originally shipped — each new addition follows the same `createFalEditor`/
`createVisionEngineer` factory pattern (Phase 3's extraction), so none of
this required touching the registry or core contracts.

**Editors (5 total, up from 2):**

- `nano-banana-pro`, `flux-2-klein-4b` — original two (US-001)
- `qwen-image-edit-2511` (Alibaba, Apache 2.0) — second open-source option,
  different lab/architecture from `flux-2-klein-4b`
- `flux-kontext-pro` (Black Forest Labs) — third paid provider, and the
  first to need `imageInputMode: "url"` (singular `image_url`, not the
  plural `image_urls` every other endpoint here uses) — the factory's
  config field for this was added and wired through correctly
- `gpt-image-1-edit` (OpenAI) — fourth paid provider

**Engineers (4 total, up from 2):**

- `passthrough`, `claude-opus-5` — original two, A/B'd in US-002
- `gpt-4o`, `qwen-vl` — both via the same `openrouter/router/vision`
  endpoint, extracted into `src/engineers/visionEngineer.ts`'s
  `createVisionEngineer()` factory (`claudeOpus5.ts` was refactored onto it
  too, for consistency)

**Verified this session** (real fal.ai/OpenRouter calls, not just
`tsc --noEmit`): all 5 editors produced correct edits on the same test
fixture (yellow square -> red circle, background preserved) — including
confirming `flux-kontext-pro`'s different request schema actually works,
not just typechecks. Both new engineers (`gpt-4o`, `qwen-vl`) correctly
grounded a vague, generation-style prompt into a precise instruction
naming the object they actually saw.

**Not yet done, and worth flagging honestly:** CLAUDE.md §6 requires a real
engineer to be "A/B'd against passthrough... kept only if it demonstrably
helps" before being trusted — that formal bar was cleared for
`claude-opus-5` in US-002 (measured pixel-level comparison). `gpt-4o` and
`qwen-vl` have only been smoke-tested for functional correctness here, not
formally A/B'd/measured against passthrough or against each other. They
work; whether either is _better_ is still an open question. Same
distinction applies to cost data: `qwen-image-edit-2511` and
`gpt-image-1-edit` deliberately ship with `costUsd` left `undefined`
(their docs explain why — per-megapixel and quality-tiered pricing,
respectively) rather than a static number that would misrepresent actual
billing, consistent with the fix applied to item #4 above.

---

## Success Criteria

**Core proven when:** ✅ done — real edit, reproduced; switching proven;
abstraction extracted from observation not imagination; engineer earns its
keep via measured A/B.

**Project "complete" has no fixed definition** — per §9, scope is earned
phase by phase, not planned upfront. Next real gate is whichever of these
happens first: a concrete need forces a Phase 5+ capability, or the
remaining open decision (what the desktop phase is _for_) gets answered.

---

## Open decisions still unresolved

- What is the desktop phase _for_? (local-GPU capability vs. packaging —
  §12; not blocking anything since the web shell already ships without it)

All other §12 decisions are now resolved and struck through in `CLAUDE.md`.

---

**Last Updated:** 2026-07-30
