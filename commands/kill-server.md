Kill the dev server for this project and optionally clean and restart it.

Usage:
- `/kill-server` or `/ks` — kill the dev server
- `/kill-server -r` or `/ks restart` — kill, then restart
- `/kill-server -c` or `/ks clean` — kill, clean build cache, restart

Steps:
1. Detect the project type and find the dev server port:
   - Check `package.json` for `devPort` field (preferred, machine-readable)
   - Check `vite.config.*` for `server.port`
   - Check `package.json` scripts for `--port` flags
   - Check running processes: `lsof -iTCP -sTCP:LISTEN -P` filtered by common dev ports
   - If multiple candidates, ask the user
2. Kill the server:
   - `kill $(lsof -iTCP:<port> -sTCP:LISTEN -t) 2>/dev/null`
3. If `-c` / `clean`:
   - Node/Vite: `rm -rf node_modules/.vite dist` (or the `clean` script if it exists)
   - Cargo: `cargo clean`
   - Python: remove `__pycache__`, `.pytest_cache`, etc.
4. If `-r` / `restart` or `-c` / `clean`:
   - Start the dev server again using the appropriate command (`pnpm dev`, `cargo run`, etc.)
   - Report the port and URL
5. Ensure auto-approve coverage for this project's port:
   - Check if `.claude/hooks/auto-approve.yml` exists in the project
   - If not, or if it doesn't cover the kill pattern for this port, offer to create/update it:
     ```yaml
     rules:
       - allow-regex: '^kill [$][(]lsof -iTCP:<port> '
     ```
   - Ask the user before writing

Setting up `devPort` in `package.json`:
- If no `devPort` field exists and you detect the port from `vite.config.ts` or similar, offer to add `"devPort": <port>` to `package.json` for future machine-readability
