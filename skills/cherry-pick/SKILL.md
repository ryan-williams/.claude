---
name: cherry-pick
description: Cherry-pick between long-lived peer branches that are parallel forks of one another (no base branch) — survey what each peer has that this branch lacks, triage against the repo's intended-delta ledger, land adapted CPs, and advance the per-pair CP cursor. Use when the user says "/cp", "/cherry-pick", "CP scramble", "pull in from cw-s3", "parity pass", "what does gcs owe upstream?". Config lives in `.claude/cp.yml`; the tool is `git cp`.
---

# `/cp` — cherry-pick across long-lived peer forks

## The pattern this serves

Some repos run **N long-lived branches that are peers, not a trunk and its children**: one branch per deployment / per fork target, each with its own real customizations, all sharing a core. A feature or fix lands on whichever branch happened to be checked out, and then has to be *adapted* onto the others. There is no merge that could ever be right — the branches are supposed to differ — so the only tool is cherry-picking, forever, in every direction.

Canonical instance: `~/c/oa/marin-gcs-usage` — `gcs`, `cw-s3` (worktree `wt/cw-s3`), and upstream `dt/main` (separate repo `~/c/disk-tree`). Its model is written up in `specs/branch-parity-discipline.md`; read that repo's ledger before triaging there.

**These are adapted CPs, not `git cherry-pick` runs.** A scramble usually lands as *one* commit per peer per pass, whose body enumerates the source SHAs, says what each contributed, and says what was skipped and why. `git cherry-pick -x` is the exception, not the rule.

## Usage

- `/cp` — the peers from the last pass on this branch (all of them, first time)
- `/cp cw-s3` — only that peer, and remembered as the default for next time
- `/cp -a` — every peer, ignoring what was remembered
- `/cp --survey` (or "just show me") — stop after the triage table, land nothing

## Step 1 — Survey

```bash
git cp                # same peers as last time; announced in the header
git cp cw-s3          # one peer (remembered)
git cp -a -f          # every peer; -f fetches the remotes behind peer refs first
git cp -v cw-s3       # also list commits that already show port evidence
git cp -j             # JSON
git cp matrix         # every pair's cursor + backlog, at a glance
```

Config is `.claude/cp.yml` at the repo root (`git cp init` scaffolds one):

```yaml
branches:
  gcs: {desc: gcs.oa.dev — GCS deployment}
  cw-s3: {desc: CoreWeave S3 deployment, worktree: wt/cw-s3}
  dt/main:
    desc: upstream disk-tree
    remote: dt
    aliases: [dt, disk-tree]     # names a cursor marker may use
    handoff: spec                # separate repo — write a CP manifest, don't cherry-pick across
    repo: ~/c/disk-tree
surfaces: [packages/react/src, src/disk_tree, job, site/src]   # parity-relevant subtrees
ledger: specs/branch-parity-discipline.md   # the intended-delta table
audit: scripts/branch-audit                 # end-of-scramble verification
```

Every branch in `branches:` is a peer of every other. If there is no config, offer to write one from the repo's actual branches — don't guess silently. (`.claude/` is usually gitignored, so a linked worktree won't carry its own copy; the tool falls back to the main worktree's.)

**The survey is a filter, not an answer.** It prunes hundreds of commits to a few dozen by looking for evidence a commit was already ported:

| mark | meaning |
|---|---|
| `=` | `git cherry` found a patch-equivalent commit already on this branch |
| `@` | the commit's abbreviated SHA is cited in one of this branch's commit bodies (the adapted-CP signal — bodies here cite their sources) |
| `~` | an identical subject already exists on this branch |

Unmarked rows are what you triage. Marked rows are hidden unless `-v`.

## Step 2 — Cursors

A cursor records, **per ordered pair**, how far along a peer this branch has assessed — ported *or deliberately skipped*. It is the survey's floor, and the only thing standing between a routine pass and re-triaging the whole fork. `git cp matrix` prints the whole grid:

```
           gcs        cw-s3      dt/main
* gcs      ·          — 17       — 81
  cw-s3    8191de0 ✓  ·          — 146
  dt/main  — 384      — 114      ·
```

Rows assess columns. `—` means no cursor, so that cell is measured from the merge-base and its count is mostly noise.

Cursors live in two places; whichever sits **further along the peer** wins:

- **Marker** — ``[CP cursor: <peer> `<sha>`]`` at the end of a commit subject, or a `CP-cursor: <peer> <sha>` trailer in the body. This is the reviewable record: it survives a clone, and it sits right next to the prose explaining what was skipped and why. Prefer it whenever the pass lands a commit.
- **Ref** — `refs/cp/<branch>%<peer>`, written by `git cp set <peer> [<sha>]`. This exists for the case a marker can't cover: **a pass that assessed a peer and correctly ported nothing** leaves no commit to mark. Without it the next pass re-derives every skip from scratch. Refs are local-only (not pushed by default), which is fine — they're an index, not the record.

```bash
git cp set cw-s3              # assessed cw-s3 up to its current tip
git cp set cw-s3 <sha>        # ...up to a specific commit
git cp set -n cw-s3           # dry run
git cp sync                   # backfill refs from existing markers (run once per repo)
```

A cursor that is no longer an ancestor of its peer (rebase) is reported and ignored rather than silently trusted.

## Step 3 — Triage

For each unmarked candidate, decide one of:

1. **Port** — real feature or fix that this branch wants.
2. **Port, adapted** — the usual case. The peer's version assumes things this branch doesn't have (a different axis, no attribution, a different serving arch). Port the idea, write it against this branch's code.
3. **Skip — intended delta.** Check the ledger (`ledger:` in the config). Branding, deployment targets, auth apps, per-deployment axes, arch differences. Nothing to do.
4. **Skip — not applicable.** Depends on data or a subsystem this branch doesn't have.
5. **Already there.** The survey missed it (the heuristics are conservative). Note it so the cursor still moves past it.

Group by surface, not by commit order — one `site/src` pass reads better than eight interleaved ones. Read the peer commits' bodies; in this workflow they are long and explain intent.

Anything you skip must be **named with a reason**. That's what makes the cursor trustworthy — a future pass must not have to re-derive why a commit was passed over.

Watch for `⇒ <target>` in the survey output: a ``[CP→<target>]`` marker on the source commit means its author already flagged it as owed to that target.

## Step 4 — Land it

Work in the branch's own worktree when the config names one (`worktree:`); don't check out over the user's current checkout.

- **Same repo**: apply the changes (by hand, or `git cherry-pick -x` when a commit genuinely applies clean and needs no adaptation), and land **one commit per peer per pass** unless the work is large enough to want splitting.
- **Cross-repo** (`handoff: spec`): do **not** cherry-pick across. Write a CP manifest under the target repo's `specs/` per the spec workflow in `~/.claude/CLAUDE.md` — source SHAs, what each needs, what's intended to stay divergent — and tell the user to run it in that repo's session.

Commit message shape, matching the established convention:

```
<what landed, in this branch's terms> [CP cursor: <peer> `<sha>`]

Adapted CP of <peer> `<a>..<b>`:

- `<sha>`: what it contributed here, and how it differs from the peer's version
- `<sha>` + `<sha>`: ...

Skipped as <peer>-only: `<sha>` (reason), `<sha>` (reason).
```

One subject can only carry one marker; when a pass covered several peers, put the rest in `CP-cursor:` trailers.

**Every peer the pass assessed gets a cursor, including the ones that produced nothing** — marker if the pass committed, `git cp set` otherwise. The cursor SHA is the peer's tip **as surveyed**, including the commits you skipped.

## Step 5 — Verify

- Run the repo's `audit:` command if configured (`scripts/branch-audit` shells out to [git-didi](https://github.com/runsascoded/git-didi) for a diff-of-diffs per branch pair × surface). Surfaces the ledger says are at parity must print `parity`; anything else is either a ledger entry or a miss.
- Re-run `git cp <peer>` — the candidate list should now be empty — and `git cp matrix` to confirm every pair you touched shows `✓`.
- Update the ledger's scramble log with what landed and what was deferred, if the repo keeps one.
- Build/test per the branch (these repos have real FEs — CIC per `~/.claude/CLAUDE.md` when the change is visible).

## Report back

Per peer: cursor moved from → to, how many ported / skipped / deferred, the commit SHA(s) created, audit result, and anything queued for the next pass in the other direction. Name the skips.
