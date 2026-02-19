Resolve Git conflicts intelligently by understanding the intent of both sides.

Flags:
- No flags (default): resolve conflicts only, leave files unstaged
- `-a`: resolve and `git add` the resolved files
- `-c`: resolve, `git add`, and continue (`git rebase --continue` or `git merge --continue` or `git cherry-pick --continue`)
- `-cc`: resolve, `git add`, continue, and if more conflicts arise (during rebase), keep resolving until the operation completes

Steps:
1. Parse flags from the user's invocation (e.g. `/resolve -c`)
2. Detect state: run `git status` to confirm we're in a conflicted rebase/merge/cherry-pick state
   - Identify the operation type (rebase, merge, cherry-pick) from status output or `.git/` state files (`REBASE_HEAD`, `MERGE_HEAD`, `CHERRY_PICK_HEAD`)
   - Identify all conflicted files (lines starting with `both modified:`, `both added:`, `deleted by us/them:`, etc.)
   - If not in a conflicted state, tell the user and stop
3. For each conflicted file:
   - Read the file to see conflict markers (`<<<<<<<`, `=======`, `>>>>>>>`)
   - Identify "ours" and "theirs" refs from the marker annotations
   - Note: during rebase, "ours" = the branch being rebased **onto** (e.g. `main`), "theirs" = the commit being replayed. This is the opposite of what you might expect.
   - If the conflict context isn't clear enough to resolve confidently:
     - Use `git log --all --oneline -- <file>` and `git log --all -p -- <file>` to find relevant commits on each side that touched the conflicted regions
     - Read surrounding code context and commit messages to understand intent
   - Resolve by merging both sides' changes semantically (not just picking one side)
   - Remove all conflict markers from the file
4. Verify: run `git diff --check` on the resolved files to confirm no conflict markers remain
   - If markers remain, fix them before proceeding
5. Present a summary: for each file, briefly describe what was resolved and how (e.g. "combined the new import from main with the function rename from the rebased commit")
6. If `-a`, `-c`, or `-cc`: stage resolved files with `git add <file>` for each conflicted file
7. If `-c` or `-cc`: continue the operation:
   - Rebase: `git rebase --continue`
   - Merge: `git merge --continue`
   - Cherry-pick: `git cherry-pick --continue`
8. If `-cc`: after continuing, check if more conflicts arose (rebase may stop again on the next commit). If so, loop back to step 3. Repeat until the operation completes successfully.

Important:
- Always read the full conflicted file before resolving; don't guess from partial context
- Prefer semantic merges that incorporate both sides' intent over picking one side
- For delete/modify conflicts, check whether the deletion or the modification better reflects the overall intent
- Use `git log` liberally to understand why each side made its changes
- Never silently drop changes from either side without explaining why in the summary
