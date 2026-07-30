# High-Level User Stories

This document tracks all user stories for Studio AI.

## Overview

| Status         | Count |
| -------------- | ----- |
| ✅ Complete    | 3     |
| 🚧 In Progress | 0     |
| 📝 Planned     | 0     |
| **Total**      | 3     |

---

## User Stories

| ID     | Title                                | Spec                                              | Plan | Status      | Commit |
| ------ | ------------------------------------ | --------------------------------------------------| ---- | ----------- | ------ |
| US-001 | Walking skeleton + switching proven  | [Link](features/us-001-walking-skeleton.md)       | -    | ✅ Complete | -      |
| US-002 | Real PromptEngineer, A/B'd (Phase 4) | [Link](features/us-002-prompt-engineer-ab.md)     | -    | ✅ Complete | -      |
| US-003 | Web frontend shell                   | [Link](features/us-003-web-shell.md)              | [Link](plans/us-003-plan.md) | ✅ Complete | -      |

---

## Status Legend

- ✅ **Complete** - Implemented, tested, and merged
- 🚧 **In Progress** - Currently being worked on
- 📝 **Planned** - Spec written, ready for implementation
- ⏸️ **Blocked** - Waiting on dependency or decision

---

## How to Use This Document

1. **Add new stories** - Create spec in `features/`, add row to table above
2. **Start implementation** - Update status to 🚧, create plan in `plans/`
3. **Complete story** - Update status to ✅, add commit hash
4. **Track progress** - Update counts in Overview section

### File Naming Conventions

**User Stories:** `features/us-XXX-short-name.md`

- Use lowercase for filenames
- Use UPPERCASE (US-XXX) in display text

**Plans:** `plans/us-XXX-plan.md`

- One plan per user story
- Links back to the user story

---

## Phases

### Phase 1: [Phase Name]

- [ ] US-001: [Story title]
- [ ] US-002: [Story title]

### Phase 2: [Phase Name]

- [ ] US-003: [Story title]
- [ ] US-004: [Story title]

---

### Phase 0/1/2 (Core walking skeleton)

- [x] US-001: Walking skeleton + switching proven

### Phase 3 (Extract, don't invent)

- [x] Provider abstraction extracted from US-001's two working adapters (no
      separate US — folded into US-001's tracking)

### Phase 4 (Prompt engineer earns its place)

- [x] US-002: Real PromptEngineer, A/B'd against passthrough

**Last Updated:** 2026-07-29
