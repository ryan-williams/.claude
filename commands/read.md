Read another local Claude session's recent history to sync context, and act on any asks directed at us.

Usage: `/read [<name>]`
- `<name>`: optional project / repo / dir identifier — substring-matches the target project's cwd.
- No arg: infer the "other" session from ambient context (see step 1).

Common pattern: two sessions pass work back and forth (often via `specs/*.md`). `/read` catches this session up on what the other has done since we last read, then executes any unambiguous asks directed at us.

## Background — how session transcripts work

- Layout: `~/.claude/projects/<encoded-cwd>/<session-uuid>.jsonl` (cwd path with `/` and `.` replaced by `-`; leading `/` → bare `-`).
- Each JSONL line is one event: keys include `timestamp`, `uuid`, `sessionId`, `cwd`, `gitBranch`, plus the message content (nested under `message`, or top-level `type`).
- Events include `user`, `assistant`, `system`, `progress`, `attachment`, `file-history-snapshot`, `permission-mode`, etc. The signal is in `user` / `assistant` — the rest is bookkeeping.
- **Compactions do not truncate the file.** Each compaction writes one line with `isCompactSummary: true` (containing the summary text, ~10–20KB) and leaves everything before it intact. Files grow cumulatively — a busy session can be tens of thousands of lines / tens of MB, spanning months.

## Identifiers you can use directly

- `$CLAUDE_CODE_SESSION_ID` — this session's UUID.
- `pwd` → derive current project's encoded dir (`/`→`-`, `.`→`-`).
- Together these tell you *your own* jsonl at `~/.claude/projects/<pwd-encoded>/$CLAUDE_CODE_SESSION_ID.jsonl` — always exclude it from candidates.

## Steps

### 1. Identify target project + session

- **With `<name>`**: `ls -td ~/.claude/projects/*/ | grep -i <name>` (excluding self's dir). If 0 or >1 match, list top matches with last-active time and ask.
- **Without `<name>`**:
  1. Prefer a project whose cwd matches a currently-running `claude` process (excluding self):
     ```bash
     ps -eo pid,command | awk '$2 ~ /claude$/ {print $1}' \
       | xargs -I{} lsof -a -p {} -d cwd -Fn 2>/dev/null | awk '/^n/{print substr($0,2)}' | sort -u
     ```
  2. Otherwise, most-recently-modified project dir under `~/.claude/projects/` besides self.
  3. If still ambiguous, list top 3–5 with `ls -lt` timestamps and ask.

Once a project is chosen, target session = its most-recently-modified `.jsonl`. Capture its `sessionId` (from any line, e.g. `head -1 <file> | jq -r .sessionId` — or just the filename without `.jsonl`).

### 2. Check the current project's `specs/` first

The other session may have written a spec directly into *our* project. Before tailing their jsonl:

- `git status --porcelain specs/ 2>/dev/null` in the current cwd.
- Any new / modified / untracked `specs/*.md` files are first-class input. Read them fully — they may contain the definitive ask, in which case the JSONL is corroborating context, not the primary source.

### 3. Read since our cursor

Cursor file: `~/.claude/state/read-cursors.json`. Shape:
```json
{
  "<reader_session_uuid>": {
    "<target_session_uuid>": {
      "last_line": <int, 1-indexed>,
      "last_timestamp": "<ISO8601>",
      "last_read_at": "<ISO8601>"
    }
  }
}
```

Read the cursor for `(reader=$CLAUDE_CODE_SESSION_ID, target=<target_uuid>)`:

- **Cursor exists** → read lines `last_line + 1` through end of file. If none, report "no new activity" and stop (still do step 2 if there were spec changes).
- **No cursor** (first read of this target from this reader):
  - Find the most-recent `isCompactSummary: true` line: `grep -n '"isCompactSummary":true' <file> | tail -1` → line number `C`.
  - Read line `C` (the pre-digested summary of everything up to that point) + all lines after it.
  - If no compaction exists (short session), read the whole file — it's small.

Save the slice you actually read to `tmp/read-<target-uuid8>.jsonl` (per CLAUDE.md — never `/tmp`), so if you need to re-scan within the same turn you don't re-read the JSONL.

### 4. Extract + report

Focus on `type: user` (their user's asks), `type: assistant` text content (what that session is proposing/doing), and recent `Write` / `Edit` / `Bash` tool_use summaries. Skip large `tool_result` payloads. Ignore any truncated final line (mid-write).

Compact brief:

- **Target**: `<readable cwd>` (session `<uuid8>`, last active `<HH:MM>`, new lines: `N`)
- **Focus**: 1–2 lines on what that session is currently doing.
- **Asks directed at us**: bulleted, verbatim quotes where possible.
- **New specs in our project**: paths from step 2.

### 5. Act (default: just do it)

- **Unambiguous asks** → start executing immediately. This is the default per user preference.
- **Ambiguous / nothing actionable** → report the summary and ask.
- **Irreversible / outward-facing** (push, publish, delete, send) → still confirm first, per CLAUDE.md.

If the workflow expects a spec round-trip (they wrote a spec, we implement + `git mv` to `specs/done/`), follow the CLAUDE.md "Spec Workflow for Cross-Project Changes".

### 6. Advance the cursor

Only after successfully reading (before or after acting — doesn't matter as long as we don't lose the line number), update `~/.claude/state/read-cursors.json`:

- `last_line` = the total line count of the target file *at read time* (not just the last one you cared about — you don't want to re-scan the boring bookkeeping lines next time).
- `last_timestamp` = the timestamp of the last event you read (from its `timestamp` field).
- `last_read_at` = now (use the `date` command; do not hardcode).

Create `~/.claude/state/` if it doesn't exist. Do the read-modify-write with a small python one-liner (`json.load` → mutate → `json.dump` with `indent=2, sort_keys=True`).

## Notes

- **Never** read this session's own jsonl in `/read` — that's this conversation, you already have it.
- Don't hallucinate cross-session coordination — if the other session is doing unrelated work, say "no asks directed at us" and stop (still advance the cursor).
- If both sessions are `/read`ing each other in a loop, the user will see it and intervene — don't try to auto-detect.
- Cursor stays valid across compactions on the target side (jsonl is never truncated), so no special handling needed.
