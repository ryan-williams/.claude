Write a spec file for work to be done in another project.

Usage: `/spec [project] [prompt...]`
- `project`: Optional path, name, or identifiable token(s) for the target project
- `prompt`: Optional description/requirements for the spec (can be detailed)

Examples:
- `/spec` — infer project and topic from conversation context
- `/spec client` — write spec for the "client" project
- `/spec client "FE/BE split"` — spec about FE/BE split for client project
- `/spec ~/c/foo-ui auth flow` — spec about auth flow in foo-ui
- `/spec use-prms allow custom base64 alphabet ordering...` — detailed requirements inline

The project arg disambiguates the target; everything after is the spec prompt/requirements.
Quotes around multi-word prompts are optional.

Based on the current conversation, we've identified changes needed in a different local project. Write a markdown spec file in that project's directory describing the work to be done, so it can be executed in a separate Claude session scoped to that project.

Steps:
1. Identify the target project directory from arguments and/or conversation context (ask if unclear)
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
