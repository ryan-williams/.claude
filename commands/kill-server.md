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
   - Prefer `kill-port` (global helper, AAG'd): bare `kill-port` auto-detects the port from `package.json` `.devPort` → `vite.config.{ts,js,mts,cts}` → `.dev-port`; or pass an explicit port: `kill-port <port>`
   - Falls back to `kill $(lsof -iTCP:<port> -sTCP:LISTEN -t) 2>/dev/null` if `kill-port` isn't installed
3. If `-c` / `clean`:
   - Node/Vite: `rm -rf node_modules/.vite dist` (or the `clean` script if it exists)
   - Cargo: `cargo clean`
   - Python: remove `__pycache__`, `.pytest_cache`, etc.
4. If `-r` / `restart` or `-c` / `clean`:
   - Start the dev server again using the appropriate command (`pnpm dev`, `cargo run`, etc.)
   - Report the port and URL
5. Auto-approve coverage:
   - `kill-port` is AAG'd globally (any args), so no per-project rule is needed when using it
   - Only fall back to per-project `^kill [$][(]lsof -iTCP:<port> ` regex if `kill-port` is unavailable

Setting up `devPort` in `package.json`:
- If no `devPort` field exists and you detect the port from `vite.config.ts` or similar, offer to add `"devPort": <port>` to `package.json` for future machine-readability
