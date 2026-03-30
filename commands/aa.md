Auto-approve: add rule(s) so the most recently prompted Bash command (or a specified command) will be auto-approved in future.

Usage:
- `/aa` — analyze the last "ask" entry from the auto-approve log and propose rules
- `/aa -g` — same, but add rules globally instead of project-specific
- `/aa <command>` — propose rules for a specific command

Steps:
1. If no command provided, read the last "ask" entry from `~/.claude/hooks/auto-approve.log`:
   - Parse the log line: `TIMESTAMP  ask  PROJECT  COMMAND`
   - Use the command and project from that line
2. Split the command into segments (same logic as the hook: `|`, `&&`, `||`, `;`, `&`, `\n`)
   - CRITICAL: The hook evaluates EACH SEGMENT independently — all must pass for the command to be auto-approved. Rules must target individual segments, NOT the whole compound command.
   - Also decompose compound commands (`for/done`, `if/fi`) into their body commands
   - Also unwrap variable assignments: `VAR=$(cmd)` → evaluate `cmd`; `export VAR=val` → safe
3. For each segment, check if it's already covered by existing auto-approve rules:
   - Load rules from both global (`~/.claude/hooks/auto-approve.yml`) and project (`.claude/hooks/auto-approve.yml`)
   - Run each segment through the matching logic
   - Report which segments are already covered (✓) and which need rules (·)
4. For each uncovered segment, propose a rule:
   - If the segment contains `$(...)` command substitution (e.g. `kill $(lsof -iTCP:3847 ...)`), shlex can't parse it → use `allow-regex:` format
     - For port-specific kills: `'^kill [$][(]lsof -iTCP:\d+ -sTCP:LISTEN -t[)]'`
     - Use `[$]`, `[(]`, `[)]` instead of `\$`, `\(`, `\)` to avoid YAML/Python escape issues
   - Otherwise, use shlex-aware `allow:` format
   - Generalize project-specific paths to `*` where appropriate
   - Keep flags and subcommands literal for safety
   - Do NOT combine multiple segments into one regex — each rule matches ONE segment
5. Present proposed rules to the user:
   - Show the full command and its segments
   - For each uncovered segment: show the segment and the proposed rule
   - Show which file will be modified
6. After user confirms, write the rules:
   - Read the target YAML file (create with boilerplate if it doesn't exist)
   - Append rules under the `rules:` key
   - Write back
7. Verify by running the original full command through the hook to confirm it would now be approved

Flags:
- `-g`: Write rules to global `~/.claude/hooks/auto-approve.yml` instead of project-specific
- Default: project-specific `.claude/hooks/auto-approve.yml` (using the project from the log entry)

Context: The auto-approve hook (`~/.claude/hooks/auto-approve-bash`) logs all decisions to `~/.claude/hooks/auto-approve.log`.
Each line: `TIMESTAMP  DECISION  PROJECT_DIR  COMMAND`

The hook splits commands into segments, then evaluates each against rules. Understanding this split-then-match architecture is essential — a rule for the whole compound command will never match, because no single segment contains the whole command.
