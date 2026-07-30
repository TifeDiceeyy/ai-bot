---
description: Create and validate implementation plan (Phase 3+3.5)
---

# Plan & Validate

Creates comprehensive implementation plan and validates before approval.

## Prerequisites

Complete `/discovery` first.

## Plan Structure

Save to: `.claude/project/plans/us-XXX-plan.md`

**10 Sections:**

1. Metadata & Requirements Summary
2. Technical Approach
3. Database Changes (SQL)
4. API Layer (TypeScript interfaces + functions)
5. Component Architecture
6. State Management
7. Edge Cases & Error Handling
8. Testing Strategy
9. Implementation Checklist
10. Effort Estimate & Risks

## Validation (Mandatory)

Before presenting plan, validate:

1. **Database** - Tables match conventions, RLS follows patterns
2. **Types** - Match database columns, proper naming
3. **Standards** - Use `development-workflow` skill to verify compliance
4. **Acceptance Criteria** - All covered in plan
5. **File Paths** - Referenced files exist

**Auto-fix issues found, add to revision history.**

## Output

```markdown
# Plan Ready: [Feature Name]

**File:** .claude/project/plans/us-XXX-plan.md
**Status:** Draft (pending approval)

## Validation Results

- Database: [Pass/Issues]
- Types: [Pass/Issues]
- Standards: [Pass/Issues]
- Criteria: [X/Y covered]

## Plan Summary

[Brief approach description]

**Approve?** Say "approve" to proceed.
```

## After Approval

1. Update plan status: Draft → Approved
2. Update user story status: In Progress
3. Run `/start-implementation`
