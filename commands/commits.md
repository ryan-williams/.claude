Analyze uncommitted changes and create one or more logical commits.

If the user provided a path after `/commits`, change to that directory first (it should be its own Git repo).
If no path provided, work in the current directory.

Steps:
1. If a path was provided:
   - Change to that directory using `cd <path>`
   - Verify it's a Git repository with `git rev-parse --git-dir`
2. Run these commands in parallel to understand the changes:
   - `git status` to see tracked modifications and untracked files
   - `git diff` to see unstaged changes
   - `git diff --cached` to see staged changes (if any)
   - `git log -5 --oneline` to see recent commit messages (for style consistency)
3. Filter out untracked files that are likely meant to stay untracked:
   - Files/dirs matching common patterns: `tmp/`, `*.log`, `*.bak`, `local/`, `debug/`, etc.
   - Files that look like persistent workspace artifacts
   - When in doubt, ask the user
4. Analyze all changes and identify logical groupings:
   - Group by feature, bug fix, refactor, or related purpose
   - Consider file proximity (same module/component)
   - Consider change type (all renames, all deletions, all new files for one feature)
   - Each group should have a coherent "why" that can be explained in one commit message
5. Present the proposed commit plan to the user:
   - List each proposed commit with its files and draft message
   - Explain the reasoning for the groupings
   - Ask for confirmation or adjustments before proceeding
6. For each approved commit (in order):
   - Stage only the files for that commit using `git add <specific files>`
   - Draft a concise commit message:
     - Use backticks around code symbols (functions, variables, file names, commands)
     - Focus on the "why" rather than just the "what"
     - Follow the style of recent commits in the repo
   - Create the commit with the message ending with:
     ```
     🤖 Generated with [Claude Code](https://claude.com/claude-code)

     Co-Authored-By: Claude <noreply@anthropic.com>
     ```
   - Verify with `git status` before moving to the next commit
7. After all commits, show `git log --oneline -n <number of commits created>` to summarize

Important:
- Use a HEREDOC for each commit message to ensure proper formatting
- NEVER use `git add -A` or `git add .`; always use explicit file paths
- Don't commit files that likely contain secrets (`.env`, `credentials.json`, etc.)
- If such files are present, warn the user
- If there are no changes to commit, say so
- Don't push unless explicitly asked
- If all changes belong together logically, it's fine to create just one commit
