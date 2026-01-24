Write a spec file for work to be done in another project.

Based on the current conversation, we've identified changes needed in a different local project. Write a markdown spec file in that project's directory describing the work to be done, so it can be executed in a separate Claude session scoped to that project.

Steps:
1. Identify the target project directory from context (ask if unclear)
2. Summarize the work to be done:
   - What problem are we solving / what feature are we adding?
   - Why is this needed? (context from current project if relevant)
   - What specific changes are required?
   - Any constraints, edge cases, or gotchas to be aware of?
   - Any related files or patterns to reference?
3. Write the spec to `<project>/.claude/specs/<descriptive-name>.md`
   - Create the `.claude/specs/` directory if needed
   - Use a descriptive filename (kebab-case, no dates)
4. The spec should be self-contained enough that someone (or Claude) working in that project can understand and implement it without needing the current conversation's context

Format:
```markdown
# <Brief title>

## Context
<Why this is needed, what problem it solves>

## Requirements
<What needs to be done, as a bulleted list>

## Implementation Notes
<Any specific approaches, patterns to follow, files to reference>

## Acceptance Criteria
<How to verify the work is complete>
```

After writing the spec, suggest how to start work on it:
```bash
cd <project-dir>
claude
# then: "Implement the spec in .claude/specs/<name>.md"
```
