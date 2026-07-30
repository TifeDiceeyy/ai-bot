---
description: Start feature implementation (Phase 4)
---

# Implementation

Implements feature based on approved plan.

## Prerequisites

Complete `/plan-and-validate` with approval.

## Process

### Step 1: Setup

1. Read plan from `.claude/project/plans/us-XXX-plan.md`
2. Update plan status: Approved → In Progress
3. Create todos from Implementation Checklist (Section 9)

### Step 2: Build (follow plan phases)

**Phase 1: Database**

- Create migrations
- Add RLS policies
- Test locally

**Phase 2: API**

- Create module
- Implement functions
- Add error handling

**Phase 3: Components**

- Create page/list/card/form
- Add loading/error/empty states

**Phase 4: CRUD**

- Wire up create/edit/delete
- Add validation

**Phase 5: Polish**

- Styling, accessibility
- Loading indicators
- Confirmation dialogs

**Phase 6: Test**

- Run manual testing checklist
- Fix bugs
- Run build/lint

### Step 3: Review (Mandatory)

**Run `/review-implementation` before commit.**

### Step 4: Commit

1. Update plan status: Complete
2. Update user story: Complete
3. Update `.claude/project/high-level-user-stories.md`
4. Create commit with user story reference

## Output

```markdown
# Implementation Complete: [Feature Name]

## Changes

- Database: [tables created]
- API: [functions implemented]
- Components: [components built]

## Commit

- Hash: [commit hash]

## Next

- Create PR
- Deploy to staging
```
