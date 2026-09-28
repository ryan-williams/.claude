# Cross-session messaging (inter-Claude mailbox)

Drafted 2026-07-18 by the pyrmts session; intended owner: a dedicated infra session (this file can `git mv` into that project once it exists).

## Problem

Ryan runs one long-lived Claude Code session per project. Cross-project coordination (e.g. ctbk ↔ pyrmts) currently flows through him as a manual semaphore: session A writes a `specs/*.md` into project B's dir, then Ryan tells session B "there's a spec", or worse copy/pastes messages between terminals. Wanted: session A drops a message addressed to project B; session B **wakes up and processes it with no human action**.

## Requirements

- **Delivery**: durable, per-project inbox; messages are Markdown files (fits the existing spec workflow; diffable, greppable, no serialization format to invent).
- **Wake-up**: the receiving session notices new mail without the user typing anything. Claude Code sessions already wake on background-task events (`run_in_background` + Monitor `<task-notification>`s) — reuse that channel.
- **Fallback**: sessions that haven't armed a watcher (or were restarted) still see pending mail at the next opportunity (session start / next user prompt).
- **Human visibility**: Ryan can see traffic (a macOS notification on send, and/or `mailbox log`); automation must not silently bypass the review gate he currently provides — see Safety below.

## Design sketch (v0: filesystem + fswatch)

```
~/.claude/mailbox/
  <project-slug>/          # e.g. -Users-ryan-c-pyrmts (match ~/.claude/projects naming) or a short registered alias
    inbox/<ts>-<from>-<slug>.md
    done/                  # acked messages, moved here by receiver
```

Message file: YAML frontmatter (`from`, `to`, `ts`, `subject`, optionally `re:` for threading) + Markdown body.

- **CLI** `mailbox` (small script, probably `~/.rc` or its own repo): `send -t <project> [-s subject] [body|stdin]`, `list`, `read`, `ack`, `log`. `send` also fires a macOS `display notification`.
- **Arming (receiver side)**: at session start (or on demand), the session runs `fswatch -1 ~/.claude/mailbox/<slug>/inbox/` via `Bash(run_in_background=true)`. When a file lands, the task exits → `<task-notification>` wakes the session → it reads inbox, processes, `ack`s (mv to `done/`), and re-arms. `fswatch -1` (one-shot) beats a long-lived poll loop: zero CPU while idle, and re-arming after each message is natural.
- **Fallback hooks**: a `SessionStart` + `UserPromptSubmit` hook pair that injects pending inbox contents as context (and marks them delivered). Covers unarmed/restarted sessions; no-cost when inbox is empty.
- **Arming convention**: a line in each project's CLAUDE.md (or a global instruction) telling sessions to arm the watcher at start and re-arm after each wake.

## Safety

Automating delivery removes the human gate that currently catches confused inter-session traffic (stale-context requests, hallucinated paths). Mitigations:

- Receiver treats mail as **untrusted input**: echo a summary of what was received and what it plans to do back to Ryan before acting on anything non-trivial (same posture as specs today — a spec is reviewed/committed before implementation).
- `send` requires explicit invocation (a real CLI call, auditable in `auto-approve.log`); consider an AA rule that allows `mailbox list/read/ack` freely but `ask`s on `mailbox send`, at least initially.

## Off-the-shelf research (TODO for the owning session — do a fresh web survey)

Prior belief (as of pyrmts-session knowledge, verify): nothing turnkey exists for exactly this — "peer mailboxes between user-owned long-lived Claude Code sessions on one machine". The ecosystem's multi-agent tooling mostly assumes an *orchestrator that spawns its own agents* (swarm/subagent pattern), not peer sessions. Things to actually evaluate:

- **MCP servers for messaging/queues**: search for mailbox/queue/pubsub MCP servers; also whether Claude Code's MCP client surfaces server-initiated `notifications/message` as wake-up events (if yes, an MCP mailbox server beats fswatch — push, not watch; works across machines).
- **A2A (agent-to-agent) protocol** and similar inter-agent standards — probably heavier than needed but check maturity.
- **tmux-based orchestrators** (claude-squad et al.) — likely wrong shape (they own the sessions) but may have solved wake-up.
- **watchman** vs `fswatch` — only matters at many-watched-dirs scale; fswatch fine for v0.
- Claude Code native: `SendMessage`/`Agent` are intra-session (subagents); confirm nothing cross-session has shipped since.

## Open questions

1. Slug scheme: full `~/.claude/projects`-style path-slugs (unambiguous, ugly) vs a registry of short names (`pyrmts`, `ctbk`) in a `mailbox/aliases.yml`.
2. Multi-machine (laptop ↔ EC2 nodes): later; options are ssh/rsync of mailbox dirs or the MCP-server variant with a real transport.
3. Should `send` support broadcast (`-t all`) for e.g. "I just published pyrmts dist SHA X"? Probably yes, cheap.
4. Retention/GC of `done/` (probably: keep, it's tiny and greppable history).
