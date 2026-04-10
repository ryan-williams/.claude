Autosquash uncommitted changes onto the appropriate ancestor commit(s).

Steps:
1. Run `git diff` and `git diff --cached` to see all uncommitted changes
2. Run `git log --oneline` to see recent commits (back to the merge base with the main/default branch, or ~20 commits, whichever is fewer)
3. For each changed file/hunk, identify which ancestor commit it most logically belongs to:
   - Read the commit messages and diffs of recent commits
   - Match changes to commits by: same file modified, same feature/topic, related code
   - A change "belongs to" a commit if it looks like a fixup, extension, or correction of that commit's work
4. Group changes by target commit:
   - If all changes belong to one commit: single fixup
   - If changes span multiple commits: multiple fixups
   - If a change doesn't clearly belong to any ancestor: ask the user
5. Present the plan:
   - Show each group: target commit, files/hunks, and why
   - Ask for confirmation
6. Execute:
   - For each target commit (oldest first):
     - Stage the relevant files/hunks (`git add <files>` or `git add -p` for partial files)
     - Create a fixup commit: `git commit --fixup=<target-sha>`
   - After all fixup commits are created:
     - Run `git rebase -i --autosquash <base>` where `<base>` is the parent of the oldest target commit
     - Use `GIT_SEQUENCE_EDITOR=true` to auto-accept the rebase todo (non-interactive)
7. Verify with `git log --oneline` showing the result

Important:
- If a file has changes belonging to multiple commits, use `git add -p` to stage hunks separately
- If the rebase would conflict, abort and report which commits conflict
- Don't autosquash onto commits that have already been pushed (unless on a feature branch where force-push is expected)
- If unsure which commit a change belongs to, ask — don't guess
