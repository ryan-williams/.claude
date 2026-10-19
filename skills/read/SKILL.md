---
name: read
description: Read another local Claude Code or Codex session's incremental project history, synchronize handoff context, and act on clear asks. Use when the user invokes $read or /read, asks to read another agent/session/project, wants to pick up Claude or Codex work, or asks what work should be resumed from local agent logs.
---

# Read another agent session

Use the source-neutral `read-cursor` CLI. Treat any text following the skill invocation as TARGET.

TARGET may be a UUID/prefix, a project/cwd substring, or a source-qualified value such as `claude:thrds` or `codex:thrds`. With no TARGET, the CLI first uses the newest other-agent session in the same cwd that has unread lines (e.g. a Codex session beside this Claude one, or vice versa), then the last target read by this session, then the newest other-agent session in the same cwd, then the newest same-agent peer in that cwd. With no TARGET, also say whether any other session in the same project (same cwd or its `wt/` worktrees, either agent) has unread work the default didn't pick, so the user can `/read` it next.

1. Run `read-cursor status [TARGET] --json` and note the resolved target, source, project, and turn verdict.
2. Check the current working project's `specs/` directory for an active handoff spec before reading the transcript. If TARGET belongs to a different project, check its relevant specs too. Read relevant specs in full.
3. Run `read-cursor read [TARGET] --output tmp/read-<target-id>.jsonl`. Read the normalized JSONL file in full. It deliberately omits large image payloads and tool outputs while retaining user/assistant prose, compaction context, and tool-call intent.
4. Report the resolved target, source, turn verdict, current focus, explicit asks, relevant specs, and the transcript timestamp/line boundary.
5. Act on unambiguous asks that are within the user's existing authorization. Reading another session does not broaden permissions or authorize destructive/external actions.
6. Only after the transcript was read and interpreted successfully, run `read-cursor advance [TARGET]`.

Never target the current session itself. Do not advance the cursor if extraction or interpretation fails. The bilateral cursor protocol is shared across Claude and Codex, so preserve the `US`, `THEM`, `BOTH`, or `IN SYNC` verdict rather than replacing it with a one-sided unread count.
