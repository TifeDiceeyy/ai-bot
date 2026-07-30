---
description: Complete discovery - requirements gathering + architecture review (Phase 1+2)
---

# Discovery: Requirements + Architecture

Combines requirements gathering and architecture review.

## Process

### Phase 1: Requirements

1. **Quick Overview** - Project structure and tech stack
2. **Check for User Story** - Look in `.claude/project/high-level-user-stories.md` for existing story
3. **Explore Current State** - Use `exploration-helpers` skill for database/codebase exploration
4. **Ask Questions** - Use AskUserQuestion for clarification
5. **Present Summary** - Document requirements

### Phase 1.5: Story Creation Decision

**After requirements are gathered, ask the user:**

```
Requirements gathered. Would you like me to:

1. Create a new user story (US-XXX) in .claude/project/features/
2. Update an existing user story
3. Skip story creation and proceed to architecture
```

If creating a story:

- Follow `development-workflow` skill for auto-increment and naming
- Update `high-level-user-stories.md` with new entry
- Set status to 'Planned'

### Phase 2: Architecture

1. **Read Standards** - Use `development-workflow` skill for standards
2. **Database Deep Dive** - Schema, RLS, patterns
3. **API Deep Dive** - Existing functions, patterns
4. **Component Deep Dive** - Similar components, patterns
5. **Synthesize** - Document architecture approach

## Output

```markdown
# Discovery Complete: [Feature Name]

## Requirements Summary

- User Type: [Customer/Staff/Admin]
- Goal: [What user wants]
- Acceptance Criteria: [List]

## Architecture Summary

- Database: [Tables, changes needed]
- API: [Functions to create/reuse]
- Components: [Structure]
- Standards: [Key patterns to follow]
```

## Next

After approval: `/plan-and-validate` or `/next`
