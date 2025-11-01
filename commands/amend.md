Amend HEAD with uncommitted changes (if any) and rewrite the commit message based on the complete set of changes.

If the user provided additional context or flags after `/amend`, respect them:
- `preserve`: The user has manually edited HEAD's commit message and wants those edits incorporated into the new message
- Any other text: Treat as additional context/instructions for the commit message

Steps:
1. Run `git status` and `git diff` (both staged and unstaged) to check for uncommitted changes
2. Run `git show HEAD` to see what's in the current HEAD commit
3. Run `git log -1 --format='%B'` to see the current commit message
4. Determine the scope:
   - If there are uncommitted changes: analyze both HEAD's existing changes plus the new uncommitted changes
   - If there are no uncommitted changes: just analyze HEAD's patches (user likely squashed commits and wants a better message)
5. Draft a new commit message:
   - If `preserve` flag: incorporate the user's manual edits from the current commit message
   - Otherwise: describe the complete amended commit as if it were being created fresh (don't frame it as an update)
   - Apply any additional user context/instructions provided
6. If there are uncommitted changes: stage them with `git add -u` (and specific untracked files if appropriate)
7. Amend the commit with: `git commit --amend -m "$(cat <<'EOF'
   <your new commit message>

   🤖 Generated with [Claude Code](https://claude.com/claude-code)

   Co-Authored-By: Claude <noreply@anthropic.com>
   EOF
   )"`
8. Run `git status` to verify success

Important:
- The new commit message should read as a de novo description of the complete amended commit, not as an incremental update
- Follow the commit message style from recent commits in the repo
- Use `git add -u` to stage modified files (not `git add -A`)
- Handle both cases gracefully: with or without uncommitted changes
