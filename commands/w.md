Watch the most recent CI run on the current branch. Works with both GitHub Actions and GitLab CI.

Steps:
1. Get the current branch name: `git branch --show-current`
2. Get the remote tracking branch to determine which remote to query:
   - `git rev-parse --abbrev-ref @{u}` to find e.g. `r/main` or `u/feat`
   - Extract the remote name (part before `/`)
   - If no tracking branch, infer the most likely remote
3. Detect SCM type from the remote URL (`git remote get-url <remote>`):
   - `github.com` → GitHub
   - `gitlab.com` (or other GitLab instances) → GitLab
4. **GitHub**: find and watch the most recent GHA run:
   - `gh run list --branch <branch-or-user-branch> -L 5 --json databaseId,status,workflowName,event,createdAt,headBranch`
   - If the branch was pushed via `gpu`, the remote branch name is `u/<prefix>/<branch>` — check both the local and remote branch names
   - Pick the most recent run (preferring in-progress over completed)
   - If in progress: `gh run watch <run-id>` to stream status
   - When done, report success/failure and show the run URL
5. **GitLab**: find and watch the most recent pipeline:
   - `glab ci list -b <branch> --per-page 5` to find recent pipelines
   - Pick the most recent (preferring running/pending over completed)
   - If in progress: `glab ci trace` to stream the job logs, or poll `glab ci view` for status
   - When done, report success/failure and show the pipeline URL
6. If no run/pipeline found:
   - Tell the user no recent CI was found on this branch
   - Suggest they may need to push first (`/pw`)
