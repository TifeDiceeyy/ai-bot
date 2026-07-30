# CLAUDE.md — Studio AI

> Version: 1.0 · Status: Operational spec (drives Claude Code)
> This is not a manifesto. It is a set of executable rules, gates, and a build order.
> If a line here cannot be acted on or checked, it does not belong here.

---

## 0. What this project is

A headless core that takes an **image + a user's plain-language request** and returns an
**edited image**, by (a) turning the request into a grounded edit *instruction* and (b) feeding
that instruction to a swappable image-editing model. Model choice is **manual and switchable**
at any time — open-source or paid API. A frontend (Telegram / web / Electron) is a thin shell
over this core and is deferred until the core works.

Not an API wrapper's opposite either: build the smallest thing that edits one real image, then
earn every layer above it.

---

## 1. Decision rule (read this before every non-trivial choice)

When two implementations are both valid, pick in **this order**. Higher wins.

1. **Correct & license-safe** — produces the right result and violates no licensing gate (§3).
2. **Working end-to-end** — a thin path that runs beats a rich path that doesn't.
3. **Simplest thing that passes the gate** — YAGNI. Do not build for imagined futures.
4. **Easiest to test.**
5. **Easiest to reason about / least coupled to any provider.**
6. **Highest edit quality**, all else equal.

> The old manifesto said "always optimize for [seven things], never write less code."
> That is not executable — those goals conflict and it has no tie-breaker. **This list is the
> tie-breaker.** "More sophisticated" is never a reason on its own.

---

## 2. The spine: 11 engineering principles (non-negotiable)

These govern *how* you work. They outrank any feature ambition.

1. **Read before you write.** Read the target before editing; read the neighbour before building.
2. **Check the world, don't assume it.** Verify versions, paths, flags, state against the live system in the same turn you assert them.
3. **A failing observation is a hypothesis, not a verdict.** Confirm a failure and name its cause before changing anything.
4. **Prove, don't eyeball.** Reproduce known-good output. Green tests are the floor, not proof it "works."
5. **Verify your own edits in a separate pass.** That pass is where your mistakes live.
6. **Make verification adversarial.** Try to make it fail. Test the refusal, not just the success. Convergent independent checks are the trustworthy signal; a lone confirmatory glance is worthless.
7. **The plan is the spine.** Externalise multi-step work as tracked tasks before the first edit. Every edit traces to a task. No opportunistic detours.
8. **Hold the scope line.** Do the job asked. Flag adjacent work; never silently expand into it. A stated constraint is the task, not an obstacle.
9. **Match the house style.** Mirror the existing pattern before inventing one.
10. **Report honestly.** Separate verified from assumed, name what didn't finish, give rollback commands. Under-claiming beats false closure.
11. **Never build generic.** For anything user-facing, work from a real reference and the right skill — never a default template. If no reference is given, ask for one; do not invent an aesthetic and call it intentional.

---

## 3. Hard gates (a gate is a STOP, not a preference)

### 3a. Licensing gate
- Only ship models cleared for the project's commercial status.
- Known state at time of writing: **FLUX.2 [klein] 4B = Apache 2.0 (commercial-OK)**. **FLUX.2 [klein] 9B and FLUX.2 [dev] = non-commercial.** Verify per model at integration — do not trust this list blindly (Principle 2).
- Every `ImageEditor` carries a `license` flag (§5). A non-commercial model may **not** enter a shippable path in a commercial build without an explicit written override from the owner.
- `OPEN DECISION`: is this project **commercial or personal**? This flag sets the entire gate. Do not proceed past Phase 1 with paid/redistributed output until it is answered.

### 3b. Verification gate
- No task is "done" until its output is reproduced (Principle 4) and checked in a separate adversarial pass (Principles 5–6).
- `tsc --noEmit` clean and the relevant test green are entry conditions to "done," never the definition of it.

### 3c. Scope gate
- Build only what the current phase's acceptance criteria require. Anything else gets logged as a flagged follow-up, not silently built (Principle 8).

---

## 4. Build order (walking skeleton first — do NOT reorder)

Each phase has a gate. You may not start a phase until the previous gate passes. Externalise
these as tracked tasks (Principle 7).

**Phase 0 — Scaffold**
Pick provider + confirm a commercial-safe model, scaffold repo, load+validate keys.
*Gate:* repo builds · `tsc --noEmit` clean · API key loads · `.env.example` documents every key.

**Phase 1 — Walking skeleton**
One hardcoded path: load image → **one** real provider call (e.g. "change background to X") → write output. No planner, no registry logic beyond a lookup, none of the engines below.
*Gate:* a real input image produces a real edited image on disk, reproduced twice. **This is GO/NO-GO for the whole concept.**

**Phase 2 — Switching, proven**
Add a **second, genuinely different** editor behind the same interface — specifically a **paid API alongside the open-source one**. Add the **passthrough** PromptEngineer (§6).
*Gate:* same input, flip the `id`, both editors return an edited image. Switching is now proven at the foundation.

**Phase 3 — Extract, don't invent**
Only now factor out the provider abstraction, generalised **from the two working adapters** and their observed differences — not from imagination.
*Gate:* a hypothetical third provider touches one file.

**Phase 4 — Prompt engineer earns its place**
Add a real (multimodal) PromptEngineer alongside passthrough and **A/B it against passthrough on real images** (§6). Keep it only if it demonstrably helps.
*Gate:* documented comparison showing the engineer improves edits on your own test images.

**Phase 5+ — Earn everything else**
Local-edit/masking, then (only if evidence demands) a quality signal that starts **human-in-the-loop**, then the **best-effort 4K upscaler** (§5a). Every engine below is admitted only when a concrete need forces it.

---

## 5. Contract: the editor seam (switching lives here)

Switching models = the registry returning a different `ImageEditor`. Nothing more.

```ts
interface EditInput { image: Buffer; instruction: string }
interface EditResult { imagePath: string; width: number; height: number; costUsd?: number }

interface ImageEditor {
  id: string;                                   // "flux2-klein-4b" | "qwen-image-edit" | "paid-api-x"
  license: "commercial-ok" | "non-commercial";  // surfaced to the picker (§3a)
  isAvailable(): boolean;                        // key present / endpoint reachable — gray out honestly
  edit(input: EditInput): Promise<EditResult>;   // costUsd rides back so switching can't silently bill
}
```

### 5a. Export & resolution (PNG always; 4K best-effort)
Two separate requirements — do not collapse them into one line:
- **Encoding: always PNG, lossless.** Fully in the app's control, independent of any model. Every download is PNG. This holds from Phase 1.
- **Resolution: best-effort, honestly labeled.** Export at the model's **true native** `width`/`height`. Verified ceilings are *below* true 4K (Qwen-Image-Edit ~2048×2048; klein ~4MP; 4K/3840×2160 is ~8.3MP), and paid endpoints vary — **re-verify per model** (Principle 2). Reaching 4K therefore requires a real **upscale pass** (super-resolution), which is a Phase 5+ capability with its own cost/latency, **not** a config flag.
- **Best-effort, not guaranteed** (owner's decision): if a model returns below 4K and upscaling is off/unavailable, ship the native-resolution PNG **labeled with its true dimensions** — never a 2K file named `...4k.png` (Principle 10). The picker/UI states the native ceiling honestly.

The "registry" is a `Map<string, ImageEditor>` with `list / select / filter-by-available`. It is
**not** a Provider Router yet and must not become one before Phase 3.

Three frictions must be **surfaced, never hidden** (this reverses the manifesto's "user never
needs to know"): **availability** (no key → not selectable), **licensing** (`license` shown, warn
on non-commercial), **cost** (`costUsd` visible so free switching can't rack up spend).

---

## 6. Contract: the prompt engineer (image + prompt → instruction)

```ts
interface EngineerInput { image: Buffer; userPrompt: string }
interface EngineerOutput { instruction: string }

interface PromptEngineer {
  id: string;  // "passthrough" | "claude" | "gpt-4o" | "qwen-vl"
  engineer(input: EngineerInput): Promise<EngineerOutput>;
}
```

Rules — these are load-bearing:

- **Output type must match the model class.** Edit models (Qwen-Image-Edit, klein-edit) want an
  **imperative instruction that names what changes AND what to preserve** — short and grounded,
  e.g. *"replace the grey wall behind her with a sunlit beach; keep her pose, hair, and lighting."*
  A generation-style prompt makes an edit model regenerate the whole frame and drift identity.
  **Precision, not verbosity.** Never emit a generation prompt to an edit model.
- **Build `passthrough` first** (raw prompt straight to the model). It is the baseline that lets
  you prove any real engineer earns its added latency and cost (Principle 4). Do not bake
  engineering in before it's measured against passthrough.
- **The engineer is multimodal** — it must see the image to ground the instruction. This merges
  the manifesto's separate Vision + Compiler stages into one honest step.
- **Guard against double-expansion.** Some models (e.g. Qwen) run their own prompt expansion by
  default (`prompt_extend: true`). When an engineer is active, **disable the model's built-in
  expansion** so there is exactly one prompt author.

### Distilling `prompt-master` (nidhinjs/prompt-master, MIT)
That repo is a **Claude *skill*** — an interactive, human-in-the-loop prompt-authoring aid. It is
**not** a runtime library and must **not** be a dependency of this app. Its *knowledge* may be
harvested into the `claude`/`gpt-4o` engineer's **system prompt**:
- its **edit-vs-generate detection** (its "Reference Image Editing" template) independently
  matches the rule above — use it as corroboration, not gospel;
- its per-image-tool profiles (comma-descriptors, negatives, weight syntax, node splits) are a
  reference for **capability-typed** adapters later (Phase 5+), not now.
Strip its clarifying-question / interactive machinery — a runtime engineer can't stop to ask.
Before lifting anything concrete, read its raw `SKILL.md`, not just the README.

---

## 7. Interface-shape decision (recorded)

Editors use the **lowest-common-denominator** shape `(image + instruction → image)` now, so any
model is swappable mid-session. Capability-typing (masks, multi-reference, ControlNet) is added
**only when a second capability class actually appears** — that is when the manifesto's
"capability registry" idea becomes correct, and not before.

---

## 8. Domain rules for edits (when actually editing)

- **Don't regenerate pixels that don't need changing.** Prefer local edits; avoid whole-image regeneration.
- **Preserve identity unless explicitly instructed otherwise:** facial structure, age, ethnicity, distinguishing marks (scars/tattoos/freckles), body proportions.
- **Plan before generate.** Generation is the last step, never the first.

---

## 9. YAGNI — do NOT build these yet

Not until a concrete, present need forces each one (then it becomes a tracked task with its own
acceptance criteria):

- Workflow Planner / Pipeline graph
- Provider Router (before Phase 3)
- Capability Registry (the typed kind)
- Mask Generator
- **Quality Evaluator + Retry Engine** — automated scoring of anatomy/hands/identity drift is
  *unsolved*; as an auto-gate it produces invented scores and retries on noise. If a quality
  signal is ever added it **starts human-in-the-loop** and an automated metric is built only
  after it's shown to correlate with the owner's own judgement.
- Event bus / dependency-injection framework
- Auto model-selection ("the software decides") — manual switching ships first; auto is a later
  feature layered on top, never the foundation.

The manifesto's "unfalsifiable" success metric ("*makes a viewer ask: was this Photoshop?*") is
**not** a stopping condition — it can only be eyeballed. Use the concrete phase gates instead.

---

## 10. Coding standards

- Strict TypeScript. No `any` unless truly unavoidable (justify in a comment).
- Small, single-responsibility modules; composition over inheritance.
- Clear interfaces; typed IPC contracts if/when a frontend process arrives.
- Unit tests for core logic; an integration test per real path.
- Exhaustive, explicit error handling; no hidden side effects.
- Secrets in `.env` only, never in code; `.env.example` lists every key with no real values.
- Match existing patterns before introducing new ones (Principle 9).

---

## 11. Reporting protocol (every handoff)

- Separate **verified** (reproduced/tested this turn) from **assumed**.
- Name what **didn't finish** and what is **BLOCKED** and why — never paper over a gap.
- Provide **rollback** commands for anything that changed state.
- Under-claim. False closure is worse than an honest "not done."

---

## 12. Open decisions (block the phases noted until answered)

| Decision | Needed by | Notes |
|---|---|---|
| ~~Commercial or personal?~~ **DECIDED: Commercial.** | — | Sets the §3a licensing gate for everything downstream. Both editors shipped in US-001 (`nano-banana-pro`, `flux-2-klein-4b`) are already commercial-safe (verified per-model at fal.ai, not assumed), so no rework needed. Any future editor must clear this gate before entering a shippable path. |
| ~~Open-source runtime: hosted API vs local GPU?~~ **DECIDED: hosted API only.** | — | No local GPU in this build. Both editors (paid and open-source) run via fal.ai. |
| ~~First paid API?~~ **DECIDED: fal.ai as aggregator**, first model `nano-banana-pro`. | — | "Many models, one key" — also serves as the host for the open-source editor and the vision-router engineer. |
| ~~Which model engineers the prompt?~~ **DECIDED: `anthropic/claude-opus-5`** via fal.ai's `openrouter/router/vision` (reuses `FAL_KEY`, no new credential). | — | A/B'd against passthrough in US-002 — demonstrably reduced shape-size drift on a generation-style prompt (591-611px vs 321-551px against a 318px expected baseline). Kept. |
| ~~Frontend target~~ **DECIDED: web first, desktop second.** | — | Core stays headless; each shell imports `core` + `adapters`, unchanged. |
| **What is the desktop phase *for*?** (local-GPU capability vs packaging) | before desktop phase | If **local GPU** → desktop hosts a `LocalGpuEditor` adapter web can't run (real feature, justifies Electron). If **packaging only** → prefer **Tauri** over Electron (fraction of the bundle, no shipped Chromium). |

Do not invent answers to these. Flag and wait (Principle 8).
