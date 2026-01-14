Analyze uncommitted changes and create a commit.

Flags:
- `-s` or `--staged`: Only commit currently staged changes (don't stage anything new)

If the user provided a path after `/commit`, change to that directory first (it should be its own Git repo).
If no path provided, work in the current directory.

Steps:
1. Parse arguments for flags (`-s`/`--staged`) and optional path
2. If a path was provided:
   - Change to that directory using `cd <path>`
   - Verify it's a Git repository with `git rev-parse --git-dir`
3. Run these commands in parallel to understand the changes:
   - `git status` to see staged, unstaged, and untracked files
   - `git diff` to see unstaged changes
   - `git diff --cached` to see staged changes
   - `git log -5 --oneline` to see recent commit messages (for style consistency)
4. Determine what to commit:
   - If `--staged` flag: only consider currently staged changes (skip step 6)
   - Otherwise: consider all uncommitted changes (staged + unstaged + relevant untracked)
5. Analyze the changes to be committed:
   - Identify the nature of changes (new feature, bug fix, refactoring, docs, etc.)
   - Don't commit files that likely contain secrets (`.env`, `credentials.json`, etc.)
   - If such files are present, warn the user
6. Stage changes (skip if `--staged` flag):
   - Use `git add -u` for modified tracked files
   - Use `git add <specific files>` for any new untracked files that should be committed
7. Draft a concise commit message:
   - Use backticks around code symbols (functions, variables, file names, commands)
   - Focus on the "why" rather than just the "what"
   - Ensure it accurately reflects the changes and their purpose
   - Follow the style of recent commits in the repo
8. Create the commit with the message ending with:
   ```
   🤖 Generated with [Claude Code](https://claude.com/claude-code)

   Co-Authored-By: Claude <noreply@anthropic.com>
   ```
9. Run `git status` after the commit to verify success

Important:
- Use a HEREDOC for the commit message to ensure proper formatting
- NEVER use `git add -A`; use `git add -u` and explicit file adds
- If there are no changes to commit, say so (don't create an empty commit)
- Don't push unless explicitly asked
