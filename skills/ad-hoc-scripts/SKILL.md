---
name: ad-hoc-scripts
description: Audit recent inline heredocs / `python -c` / bash one-liners run during recent sessions and identify chunks that should be factored into a CLI subcommand (existing or new) instead of re-inlined each time. Use when the user says things like "any ad-hoc scripts to factor out?", "review inline scripts", "what did I keep re-writing as heredocs?", "/ad-hoc-scripts", "/ahs". Distinct from `/aa-audit`: that one finds *simple safe* commands that could be silently allowed; this one finds *complex* commands where the right answer is to build a reusable CLI so the pattern isn't re-invented (and the resulting CLI is easier to AA than the underlying heredoc).
---

# Ad-hoc script audit

Goal: scan recent Bash invocations for inline heredocs / long `-c` scripts / chained ad-hoc pipelines, group by "same idea implemented multiple times", and propose factoring each into a CLI subcommand or a new script — per the "Prefer CLI subcommands over ad-hoc scripts" rule in `~/.claude/CLAUDE.md`.

The point is NOT to auto-approve more heredocs (that's `/aa-audit`'s job for the safe cases, and heredocs are usually correctly gated on `ask`). The point is: **each recurring heredoc is a missing CLI**. Once it's a CLI, one AA rule allows all future invocations, review is easier, and the logic lives in a version-controlled file rather than being re-typed by the model each session.

## Procedure

### 1. Read recent invocations

Pull `ask` entries from the AA log (heredocs and complex commands overwhelmingly hit `ask`, so this is the richest source):

```bash
grep '  ask  ' ~/.claude/hooks/auto-approve.log | tail -200
```

Adjust the tail count to the requested window (200 covers a busy week; use 500+ for "last month"). If the user names a time window, filter by the leading timestamp.

Also consider `allow` entries when the user hints that they're already AAG'ing heredocs (rare) — those are *worse* signal because there's no friction to remind them, so recurring ones can hide.

### 2. Filter to inline-script candidates

Keep only rows whose command is plausibly a "script inlined into a shell call". Signals:

**Heredocs** — nearly always candidates:
- `python3 <<'PY' ... PY` / `python <<PY ... PY` / `bash <<'BASH' ... BASH`
- `sqlite3 <db> <<'SQL' ... SQL` / `psql ... <<SQL`
- `cat > tmp/foo.py <<'PY' ... PY` (write-then-run pattern)

**Long `-c` strings** — usually candidates:
- `python -c "..."` / `python3 -c "..."` where the string is >~120 chars or has `\n`
- `node -e "..."` similar
- `bash -c "..."` where the inline is nontrivial

**Multi-segment pipelines with real logic** — sometimes candidates:
- Long `awk` / `sed` / `jq` programs (>~80 chars in a single filter)
- Chained `for` loops in `bash -c`
- Compound `git` prep loops (`for f in ...; do git log ... $f; done`) that recur

**Skip** — not a "script", or unlikely to factor:
- Genuinely one-shot debug pokes with no reusable shape (e.g. `python -c "import foo; print(foo.__version__)"` — the value is in the exploration, not the code)
- Simple `curl | jq '.x'` — already the right shape
- Compound `&&`-chains of well-known CLIs (e.g. `pnpm build && pnpm test`) — that's just workflow, not a script

### 3. Bucket by "same idea"

Look for shape similarity, not exact match. Two heredocs are "the same idea" if:
- They open the same DB / read the same log / hit the same API
- They compute a similar summary (row counts, group-bys, cost aggregation, etc.)
- The user re-typed a variant they wrote yesterday

Cluster by:
- **Same project directory** (from the AA log's project column) — highest signal for "should be a subcommand of *this* project's CLI"
- **Same tool being scripted** (e.g. always poking `~/.agentsview/sessions.db` → belongs in `agentsview` CLI)
- **Same cross-project shape** (parsing Parquet / diffing files / summarizing a log) — candidate for a global CLI (`utz`, `dffs`, `juq`, `pqa` family)

Even a bucket of 1 is worth flagging if the heredoc is >~15 lines — that's a script that ought to live in a file.

### 4. Propose factoring

For each bucket, decide the natural home:

- **Existing project CLI**: check the project for a top-level CLI (look at `pyproject.toml` `[project.scripts]`, `bin/`, a `<name>` symlink in `PATH`, or the CLAUDE.md hint list `tomat <sub>`, `ctbk <sub>`, `dffs <sub>`). Propose the subcommand path: `tomat runs summary --by project`, `agentsview db exec ...`, etc.
- **Existing utility CLI**: `utz` for general helpers, `juq` for Jupyter, `dffs` for diffs, `pqa`/`pqs`/etc. for Parquet, `iris` inside tomat, etc.
- **New CLI**: if nothing fits and the shape recurs, suggest a new one — name it, sketch the subcommand tree.
- **Keep ad-hoc**: if it really is one-shot and the shape won't recur, say so explicitly (don't just omit).

Also flag the AA payoff for each proposal: once factored, what single AA rule allows all future invocations? (e.g. `agentsview db: [exec, dump]` covers all future DB pokes.) This closes the loop with `/aa-audit`.

### 5. Present as a table

Group by proposed home:

```
Existing CLI: agentsview
| Count | Sample (first line) | Proposed subcommand | AA rule |
|-------|---------------------|---------------------|---------|
| 4     | sqlite3 ~/.agentsview/sessions.db "SELECT project, ..." | agentsview db query <sql> | `agentsview db: [query]` |
| 2     | python3 <<'PY' import sqlite3 ...                     | agentsview usage tail --project <p> | (extends existing usage) |

New CLI: (none)

Keep ad-hoc:
| 1 | python -c "import torch; print(torch.__version__)" | truly one-shot |
```

Include a one-line summary at the top: N rows scanned, M candidates, K buckets proposed.

### 6. Hand off

Do NOT implement the factoring — the point is to surface the pattern for the user to decide on. When they pick one, next steps are usually:

- If existing CLI: open the CLI's repo, add the subcommand, wire it into `[project.scripts]` / `bin/`.
- If new CLI: propose the repo layout, then let the user decide whether to bootstrap it inline or in a separate session.
- Consider a `/spec` for cross-project work (writing the subcommand in the CLI's own repo from this session).

If the user picks something to factor immediately, transition into that work — but don't collapse the audit prematurely to "and here's the code".

## Common pitfalls

- **Over-aggressive bucketing.** Two heredocs that both open SQLite are not necessarily the same idea. Only cluster when the *semantic* target is the same (same DB, same aggregation family).
- **Missing the "why". ** The value of factoring is: (1) code review the CLI once, not each session, (2) one AA rule vs many prompts, (3) don't re-type from scratch. Frame each proposal in those terms — not just "this recurs".
- **Skipping tiny recurrences.** A 5-line heredoc that recurs 6 times a week is a bigger win than a 40-line one-off. Don't only flag the long ones.
- **Ignoring the CLAUDE.md hint list.** If a project already has a top-level CLI mentioned in CLAUDE.md, that's the home — don't propose a new one.
- **Treating `cat > tmp/foo && python tmp/foo` as ad-hoc.** That's already the "write to a file" refactor of a heredoc; the real fix is to make the CLI take the args directly rather than re-writing a script each time.

## Reference

- Log: `~/.claude/hooks/auto-approve.log` (columns: `TIMESTAMP  DECISION  PROJECT  COMMAND`)
- Companion skill: `/aa-audit` for read-only single-line commands (opposite failure mode: too much friction on safe stuff)
- Related CLAUDE.md rule: "Prefer CLI subcommands over ad-hoc scripts" — this skill is the retrospective auditor for that rule
