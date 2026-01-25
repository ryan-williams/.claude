Add a command to this project's allowed permissions.

Usage: `/bless <command>`

Examples:
- `/bless npm run dev` → adds `Bash(npm run dev:*)`
- `/bless curl https://api.example.com` → adds `Bash(curl https://api.example.com:*)`
- `/bless python scripts/test.py` → adds `Bash(python scripts/test.py:*)`

Steps:
1. Parse the command from arguments (everything after `/bless`)
2. Format as `Bash(<command>:*)`
3. Add to `.claude/settings.local.json` under `permissions.allow`:
   - Create the file/directory if needed
   - Skip if already present
   - Use `jq` to update the JSON
4. Report what was added
5. Remind user to restart Claude for it to take effect: `claude -c`

Important:
- The `:*` suffix allows any arguments after the base command
- Always wrap in `Bash(...)` unless it's a different tool type (WebFetch, Read, etc.)
- If no argument provided, ask what command to bless
