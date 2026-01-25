Add a command to this project's allowed permissions.

Usage: `/bless <command>`

Examples:
- `/bless npm run dev` → adds `Bash(npm run dev:*)`
- `/bless curl https://api.example.com` → adds `Bash(curl https://api.example.com:*)`
- `/bless python scripts/test.py` → adds `Bash(python scripts/test.py:*)`

Run `bless-cmd "<command>"` to add the permission. If no argument provided, ask what command to bless.
