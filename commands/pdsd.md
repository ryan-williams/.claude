A dependency was just updated (via `pds l` or `pds g`) — retry what you were doing with the fix in place.

Context: The user has been working on something that required a change in a dependency. They:
1. Identified the issue in the dep
2. Wrote a spec / switched to the dep project to fix it
3. Came back and ran `pds l <dep>` (local) or `pds g <dep>` (GitLab/GitHub dist branch) to point this project at the updated dep
4. Now want you to pick up where you left off, using the updated dep

Steps:
1. Check what changed: `pds status` to see which deps are local vs published
2. Look at conversation history for what you were trying to do before the dep issue came up
3. If the dep was pointed at a local build (`pds l`):
   - Check that the local dep has been rebuilt (`pnpm build` or similar in the dep dir)
   - If not, suggest rebuilding
4. Restart the dev server if one was running (the dep change likely requires a restart)
5. Re-attempt whatever was failing before:
   - Re-run the failing command / test / build
   - Verify the fix resolved the issue
6. If it works, continue with the original task
7. If it doesn't, diagnose whether:
   - The dep fix didn't address the issue (may need another spec)
   - The dep needs to be rebuilt
   - The local project needs additional changes to use the dep's fix
