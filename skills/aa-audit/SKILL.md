---
name: aa-audit
description: Audit recent `ask` entries in the auto-approve log to identify Bash commands that could be auto-approved. Use when the user says things like "check AA log for AAGs", "audit AA log", "any cmds we should AAG?", "look at AA log for new rule candidates". Distinct from `/aa` (single most-recent rejected command) — this is a batch audit of N recent asks across many sessions/projects.
---

# AA log batch audit

Goal: scan recent `ask` entries in `~/.claude/hooks/auto-approve.log`, identify commands that *should* be auto-approved (read-only / informational / safe), and propose rules to the user.

## Procedure

### 1. Read recent asks

```bash
grep '  ask  ' ~/.claude/hooks/auto-approve.log | tail -60
```

Tail count is rough — use 30–100 depending on how active the user has been. If they specify a window ("last day", "since lunch"), filter by timestamp.

Also check a remote host if the user mentions one (`ssh <host> 'grep "  ask  " ~/.claude/hooks/auto-approve.log | tail -60'`). Remote hosts often have stale rules; flag that as the first finding if true.

### 2. Categorize each ask

For each row, decide which bucket it falls in:

**Skip — expected to ask, not AAG candidates:**
- Heredocs writing files: `cat > tmp/foo <<'X'`, `python3 << 'PY'`, `bash <<'BASH'`
- Git mutations: `git add ... && git commit`, `git push`, `git push -f`, `git reset --hard`, `git rebase -i`
- File mutations: `rm`, `sed -i`, `cp -r`, `mv` (outside trivial cases), `chmod` of system paths
- Process control: `kill PID`, `kill -<sig>`, `scancel`, `sbatch` (consumes resources)
- Env mutations: `uv sync`, `uv add`, `pip install`, `vsw`, `spd`
- Credentials/secrets: `gcloud auth print-access-token`, anything dumping a token
- Compound commands where *one* segment is dangerous (e.g. `... && kill -0 PID && ...`) — flag the blocking segment, not the whole pipeline

**Strong candidates — read-only / informational:**
- `<tool> --help`, `<tool> --version`, `<tool> list`, `<tool> show`, `<tool> get`
- Schema/introspection: `gws schema`, `terraform show`, etc.
- Status queries: `squeue`, `sacct`, `sinfo`, `gh run view`
- Pure inspection of cloud resources: `gcloud projects list`, `aws s3 ls`, `modal app list`

**Borderline — flag for user, don't auto-propose:**
- Commands that print credentials/tokens (read-only but sensitive)
- `kill -0 PID` (process-exists check; safe in itself but adjacent to destructive `kill`)
- Anything that mutates *external* state but is the user's normal workflow (e.g. `sbatch`, `git push`)

### 3. Check coverage before proposing

For each strong candidate, **confirm it's not already covered** before listing it. Run:

```bash
aa-test '<exact command>'
```

If `aa-test` returns `allow`, the command IS already covered — don't propose a rule for it. The ask in the log was likely from a session running stale rules (engine or YAML reloaded after the ask). Note this in your report ("would now allow with current rules") rather than re-proposing.

For project-scoped commands (e.g. `modal run scripts/foo.py` in `~/c/oa/tomat`), set `CLAUDE_PROJECT_DIR`:

```bash
CLAUDE_PROJECT_DIR=/Users/ryan/c/oa/tomat aa-test '<command>'
```

### 4. Group and propose

Group candidates by command family (e.g. all `modal *`, all `gws *`). Present as a table:

| Command | Proposed rule |
|---------|---------------|
| `modal app list [--json]` | `modal app: [list]` |
| `gws schema <name>` | `gws schema: ~` |

Pick rule format based on subcommand structure:
- `tool: [verb1, verb2]` — when there's a fixed set of safe verbs
- `tool subcmd: ~` — when *any* further args are read-only (e.g. `gws schema <name>` — all schemas are safe to print)
- `tool subcmd: [verb]` — restrict to specific verbs (e.g. `modal billing: [report, --help]`)

Add `--help` to alternation lists when you AAG the verb itself, otherwise `tool subcmd --help` regresses.

Always also list:
- **Borderlines** — separate section, ask the user yes/no per item
- **Already covered** — short note, no action needed

### 5. Decide global vs project

- **Global** (`~/.claude/hooks/auto-approve.yml`): tools used in many projects, behaviors that don't depend on project specifics (`modal --help`, `gws schema`, SLURM read-only)
- **Project** (`<repo>/.claude/hooks/auto-approve.yml`): commands referencing project-specific paths, scripts, or resource names (e.g. `modal run scripts/<this-project>/...`, `aws s3 cp s3://<this-project>-bucket/...`)

If the project file doesn't exist, offer to create it. If it exists but is malformed (missing `rules:` key, etc.), the engine now warns — surface that in the audit.

### 6. Apply and verify

After user confirms:
1. Edit the relevant YAML file (use `Edit` tool)
2. Re-run `aa-test` on each original failing command to confirm it now `allow`s
3. Spot-check a few negative cases (mutating variants like `<tool> delete`, `<tool> stop`) to confirm they still `ask`
4. Run the test suite if you modified the global file: `uv run pytest tests/`

### 7. Common pitfalls

- **Multi-token list entries** must be separate strings: `[run scripts/*, volume list]` — each entry is parsed via `parse_pattern` (post Apr 2026 fix). On stale engines, only single-token alternation works.
- **Trie list `[v1]` allows the bare prefix too**: `modal billing: [report]` allows both `modal billing` and `modal billing report …`.
- **Globs need `*` literally**: `run scripts/` (no glob) won't match `run scripts/foo.py`. Write `run scripts/*`.
- **End anchors break with redirects**: `cmd $` doesn't match `cmd 2>&1` because `2>&1` is an extra token. Use `(\s|$)` in regex form instead.
- **Stale remote rules**: if asks come from `ssh` or remote sessions, the remote may have an older copy of the engine + rules. Recommend syncing before adding new rules to fix problems that don't exist on current code.

## Reference

- Engine: `~/.claude/hooks/auto_approve.py`
- Global rules: `~/.claude/hooks/auto-approve.yml`
- Log: `~/.claude/hooks/auto-approve.log`
- Single-command companion: `/aa` (last ask), `/aag` (last ask, global), `/bless <cmd>` (specific command)
- Test helper: `aa-test '<cmd>'` (set `CLAUDE_PROJECT_DIR` for project rules)
