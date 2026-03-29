Analyze a Bash command (or pipeline) and propose auto-approve rules for it.

Usage: `/bless <command>` or `/bless` (to analyze the most recently prompted command)

Steps:
1. Parse the command: split on unquoted `|`, `&&`, `||`, `;` into segments
2. For each segment, determine which parts should be generalized vs. literal:
   - The base command (e.g. `rm -rf`, `git init`, `dvx add`) is usually kept literal
   - Path arguments that look project-specific should be wildcarded to `*`
   - Flags are usually kept literal (they affect safety)
   - Redirections (`2>&1`, `>/dev/null`) are stripped (they're not part of shlex tokens)
3. Check which segments are already covered by existing rules in `~/.claude/hooks/auto-approve.yml`
   - Only propose rules for segments that are NOT already auto-approved
4. For each uncovered segment, draft a rule:
   - Use the shlex-aware pattern syntax (not regex), unless the pattern genuinely needs regex
   - Decide scope: should it be in the global `~/.claude/hooks/auto-approve.yml` or project-specific?
   - Err toward global for general tools; project-specific for project-specific commands
5. Present the proposed rules to the user, showing:
   - The original segment and what it would match
   - Where it would be added (global vs project, and which section of the YAML)
   - Any segments already covered (skip these)
6. After user confirms, write the rules:
   - Read the target YAML file
   - Insert rules in the appropriate section (or create a new section if needed)
   - Write back the file
7. Optionally, test the new rules by running the original command through the hook

Important:
- Never auto-approve `rm` on paths that could be dangerous (outside build artifacts / tmp)
- For `cd`, `git init`, `mkdir -p`, consider whether they're genuinely safe in context
- When in doubt, propose a more specific rule and let the user decide to broaden it
- Show the user exactly what patterns will match before writing anything
