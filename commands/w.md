Watch the most recent CI run on the current branch.

Steps:
1. Get the current branch name: `git branch --show-current`
2. Get the remote tracking branch to determine which remote to query:
   - `git rev-parse --abbrev-ref @{u}` to find e.g. `r/main` or `u/feat`
   - Extract the remote name (part before `/`)
   - If no tracking branch, infer the most likely remote
3. Get the GitHub repo for that remote: `gh repo view --json nameWithOwner -q .nameWithOwner` (or parse from `git remote get-url <remote>`)
4. Find the most recent run on this branch:
   - `gh run list --branch <branch-or-user-branch> -L 5 --json databaseId,status,workflowName,event,createdAt,headBranch`
   - If the branch was pushed via `gpu`, the remote branch name is `u/<prefix>/<branch>` — check both the local and remote branch names
   - Pick the most recent run (preferring in-progress over completed)
5. If a run is found:
   - Show its workflow name, status, and URL
   - If it's still in progress: `gh run watch <run-id>` to stream status
   - When done, report success/failure
6. If no run found:
   - Tell the user no recent runs were found on this branch
   - Suggest they may need to push first (`/pw`)
