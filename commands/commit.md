Flexible Git workflow command supporting a pipeline of phases.

## Usage
- `/c` — commit (default, same as `/commit`)
- `/c <phases>` — run phases in order
- `/c <phases> <workflow-hint>` — run phases, with a hint for GHA workflow dispatch

## Phases
A phases string is a sequence of characters from `{t, c, a, s, p, d, w}`:
- `t` = **test**: run the project's test suite before proceeding (infer: `pytest`, `pnpm test`, `cargo test`, etc.)
- `c` = **commit**: create a new commit (per `/commit` conventions)
- `a` = **amend**: amend HEAD (per `/amend` conventions)
- `s` = **staged**: only commit staged changes (modifies `c` phase; like `/commit --staged`)
- `p` = **push**: push to remote
  - Uses `gpu` (push to user branch) if the branch looks like a feature/working branch
  - Uses `git push` if the branch already tracks a remote
  - Force-pushes (`gpuf` / `git push -f`) if `a` (amend) was in the phases
- `d` = **dispatch**: trigger a GHA workflow
  - If a workflow hint is provided (second arg), use `ghwr <hint>` for fuzzy-matching
  - If no hint, look for a single `workflow_dispatch`-enabled workflow; if ambiguous, ask
  - Pass `--no-open` since we'll watch via `w` phase (or the user can open manually)
- `w` = **watch**: watch the just-dispatched GHA run via `gh run watch`, then report the result

## Constraints
- `c` and `a` are mutually exclusive (error if both present)
- `s` only applies if `c` is present (error otherwise)
- `d` requires that a push happened (either `p` in phases, or branch already up-to-date with remote)
- `w` requires `d` (nothing to watch without a dispatch)
- If any phase fails, stop and report the error (don't continue to subsequent phases)

## Detecting phases mode
If the first non-flag argument matches `^[tcaspdw]+$` (and isn't a filesystem path), treat it as a phases string. Otherwise, fall back to default commit behavior (pass all args through to `/commit` logic).

## Phase execution details

### Test (`t`)
- Detect test framework from project files (`pyproject.toml` → pytest, `package.json` → pnpm test, `Cargo.toml` → cargo test, etc.)
- Run tests; abort pipeline if tests fail

### Commit (`c`) / Amend (`a`)
- Follow the same conventions as `/commit` and `/amend` respectively
- Stage changes, draft message, create commit

### Push (`p`)
- Determine push method:
  1. Check if branch has a remote tracking branch (`git rev-parse --abbrev-ref @{u}`)
  2. If yes: `git push` (or `git push -f` if amending)
  3. If no: `gpu` (or `gpuf` if amending) to push to user branch namespace
- Before pushing, verify there are commits to push (compare with upstream if tracking)

### Dispatch (`d`)
- Run: `ghwr <workflow-hint> --no-open` (or `github-workflows.py run <hint> --no-open`)
- If no hint provided, check `.github/workflows/` for `workflow_dispatch`-enabled workflows
- If exactly one found, use it; if multiple, list them and ask the user
- Capture the run ID from ghwr output for the watch phase

### Watch (`w`)
- After dispatch, find the just-triggered run:
  - Parse the run ID from the dispatch phase's output, or
  - Use `gh run list -w <workflow> -L 1 --json databaseId` to find the latest run
- Run `gh run watch <run-id>` to stream status
- When done, report success/failure and show the run URL

## Default behavior (no phases string)
When invoked as just `/c` with no phases argument (or with flags like `-s`), behave exactly like `/commit`:
- `/c` = `/commit`
- `/c -s` = `/commit --staged`
- `/c path/to/repo` = `/commit path/to/repo`
