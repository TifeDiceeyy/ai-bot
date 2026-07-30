---
description: Review completed implementation (Phase 4.5 - MANDATORY before commit)
---

# Implementation Review

Comprehensive validation before commit. **Mandatory step.**

## When to Use

- After implementation, before commit
- After fixing issues from previous review

## Validation Checklist

### 1. Database

- Migrations match plan Section 3
- Tables, columns, constraints correct
- RLS policies implemented
- Migration tested

### 2. API Layer

- All functions from plan Section 4 exist
- Signatures match plan
- Error handling present
- JSDoc comments added

### 3. Types

- Interfaces match database columns
- Proper naming (PascalCase/camelCase)
- Enums match constraints

### 4. Components

- All components from plan Section 5 exist
- Loading/error/empty states
- Form validation
- Accessibility (ARIA, keyboard nav)

### 5. Standards

- Use `development-workflow` skill to verify
- Naming conventions
- Error handling patterns
- Import order

### 6. Acceptance Criteria

- Read user story from `.claude/project/features/us-XXX-name.md`
- Map each criterion to implementation
- Verify edge cases handled

### 7. Tests

- Unit tests for API
- Component tests
- Run test suite

### 8. Build

```bash
npm run build
npm run lint
npm run type-check
```

## Output

```markdown
# Review: [Feature Name]

## Results

- Database: [Pass/Fail]
- API: [Pass/Fail]
- Types: [Pass/Fail]
- Components: [Pass/Fail]
- Standards: [Pass/Fail]
- Criteria: [X/Y met]
- Tests: [Pass/Fail]
- Build: [Pass/Fail]

## Issues Found

[List with fixes needed]

## Status: [READY / NOT READY]
```

## After Pass

Proceed with commit in `/start-implementation`.
