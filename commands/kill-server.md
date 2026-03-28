Kill the dev server for this project and optionally clean and restart it.

Usage:
- `/kill-server` — kill the dev server
- `/kill-server -r` or `/kill-server restart` — kill, then restart
- `/kill-server -c` or `/kill-server clean` — kill, clean build cache, restart

Steps:
1. Detect the project type and dev server setup:
   - Check for `package.json` → node/pnpm project, look for `dev`/`start` script
   - Check for `vite.config.*` → Vite project
   - Check for `Cargo.toml`, `pyproject.toml`, etc.
2. Find the dev server port:
   - Check `vite.config.ts` for `server.port`
   - Check `package.json` scripts for `--port` flags
   - Check running processes: `lsof -i -P | grep LISTEN` filtered by project dir or common ports
3. Kill the server:
   - `kill $(lsof -ti :<port>)` if port is known
   - Otherwise, find the process by project directory and kill it
4. If `-c` / `clean`:
   - Node/Vite: `rm -rf node_modules/.vite dist` (the `clean` script if it exists)
   - Cargo: `cargo clean`
   - Python: remove `__pycache__`, `.pytest_cache`, etc.
5. If `-r` / `restart` or `-c` / `clean`:
   - Start the dev server again using the appropriate command (`pnpm dev`, `cargo run`, etc.)
   - Report the port and URL
