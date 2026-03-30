Check for spec files in this project and work on them.

Steps:
1. Look for spec files in `specs/` (and `.claude/specs/` for older convention):
   - `ls specs/*.md .claude/specs/*.md 2>/dev/null`
   - Separate into "done" (already in `specs/done/`) and "pending" (not)
2. If any pending specs look completed (based on the current state of the code — check if the acceptance criteria / requirements are met):
   - Show which specs appear done and why
   - Offer to move them to `specs/done/` (with `git mv` if tracked, `mv` otherwise)
   - Commit the move alongside any related code changes if appropriate
3. For remaining pending specs:
   - If there's exactly one: read it and start implementing
   - If there are multiple: list them with a one-line summary each, ask which to work on
   - If there are none: say so
4. When implementing a spec:
   - Read the full spec file
   - Follow its requirements and implementation notes
   - Make commits as work progresses (intermediate commits that update the spec in-place if it spans multiple commits)
   - When done: update the spec to reflect any changes that came up during implementation, move to `specs/done/`, and commit that alongside the final code changes
