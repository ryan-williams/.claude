I've just returned to this session after being away. Context may have been compacted, so re-orient yourself before answering.

Usage:
- `/back` — I'm back, catch me up
- `/back <duration>` — I've been away for `<duration>` (e.g. `30m`, `2h`, `overnight`) — useful if any time-sensitive state (running jobs, CI, etc.) may have changed

Produce a short status brief, in roughly this shape:

1. **Where we left off** — one or two lines on the last concrete thing that happened (last commit, last tool result, last decision).
2. **Current state** — what's committed / uncommitted / pushed / in-flight. Run `git status` and `git log -5 --oneline` if useful. If a duration was given and it's long enough to matter, also check: CI runs (`gh run list -L 3` / `glab ci list`), background tasks, dev servers.
3. **Outstanding / next up** — the unfinished items from the plan or conversation. Distinguish:
   - Blocked on me (decision, input, approval)
   - Blocked on something external (CI, a long job, a review)
   - Ready to continue autonomously
4. **Suggested next step** — one concrete thing to do next, phrased so I can say "yes" or redirect.

Keep it tight — aim for under 15 lines total. Skip sections that have nothing to report rather than padding them. If the session state is genuinely clean (nothing pending), say so in one line.

If "AFK mode" was active (see `/afk`), exit it unless I re-invoke it.
