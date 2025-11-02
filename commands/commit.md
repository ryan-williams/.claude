Analyze uncommitted changes and create a commit.

If the user provided a path after `/commit`, change to that directory first (it should be its own Git repo).
If no path provided, work in the current directory.

Steps:
1. If a path was provided:
   - Change to that directory using `cd <path>`
   - Verify it's a Git repository with `git rev-parse --git-dir`
2. Run these commands in parallel to understand the changes:
   - `git status` to see all untracked files
   - `git diff` to see both staged and unstaged changes
   - `git log -5 --oneline` to see recent commit messages (for style consistency)
3. Analyze all changes:
   - Identify the nature of changes (new feature, bug fix, refactoring, docs, etc.)
   - Don't commit files that likely contain secrets (`.env`, `credentials.json`, etc.)
   - If such files are present, warn the user
4. Draft a concise commit message:
   - Use backticks around code symbols (functions, variables, file names, commands)
   - Focus on the "why" rather than just the "what"
   - Ensure it accurately reflects the changes and their purpose
   - Follow the style of recent commits in the repo
5. Stage changes:
   - Use `git add -u` for modified tracked files
   - Use `git add <specific files>` for any new untracked files that should be committed
6. Create the commit with the message ending with:
   ```
   🤖 Generated with [Claude Code](https://claude.com/claude-code)

   Co-Authored-By: Claude <noreply@anthropic.com>
   ```
7. Run `git status` after the commit to verify success

Important:
- Use a HEREDOC for the commit message to ensure proper formatting
- NEVER use `git add -A`; use `git add -u` and explicit file adds
- If there are no changes to commit, say so (don't create an empty commit)
- Don't push unless explicitly asked
