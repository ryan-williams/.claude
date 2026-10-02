---
name: tee
description: "Tee up" a web-console task in Chrome for the user to finish — open a tab in the right Chrome profile, do every step up to the final Save / Create / Confirm, then hand off. Use when the user says `/tee`, "tee it up", "set it up in chrome and I'll click save", or similar, typically right after Claude asked them to do something in a web UI (GCP OAuth clients, Cloudflare API tokens, GitHub apps/tokens, DNS records, …).
argument-hint: "[optional description / context]"
---

# `/tee` — tee up a browser task for the user to finish

Usage: `/tee [description]`

The user typically invokes this right after **you** asked them to do something in a web console ("create an OAuth client with redirect URI …", "make a CF API token with R2 edit on bucket X", …). Instead of doing it by hand, they want you to drive Chrome as far as you safely can, then stop at the last irreversible click so they can review and commit it.

## 1. Identify the task

- **With args**: the args describe the task (may be terse; combine with conversation context).
- **No args**: the task is the most recent thing you asked the user to do in a browser / web console. Look back through your recent messages for instructions like "go to …", "create …", "add … in the dashboard".
- Collect every concrete value the task needs from context: names, project / account IDs, redirect URIs, origins, scopes / permissions, resource scoping (buckets, zones), TTLs / expiry. Prefer the exact strings you already gave the user.
- If two or more candidate tasks are plausible, or a value that matters is missing, ask **one** short question (AskUserQuestion) — otherwise don't ask, just go.

## 2. Pick the Chrome profile

The task is identity-scoped by definition, so follow CLAUDE.md's "Picking the right Chrome profile":

1. Infer the identity from the task + project (OA work → `openathena`, HCCS → `hudcostreets`, personal / runsascoded → `runsascoded`, …; the target account/org/project ID in the task is the strongest signal).
2. `chrome-profiles <query>` → confirm exactly one match; `chrome-profiles -i <query>` for the bare deviceId.
3. `list_connected_browsers` / `select_browser` with that deviceId. If that profile isn't connected, say so and ask the user to open it (or run the `switch-browser` flow) — don't fall back to another profile.
4. **Say which profile/email you selected** in your first message after selecting.

## 3. Open a fresh tab and navigate

- `tabs_create_mcp` — never hijack one of the user's existing tabs.
- Navigate to the **deepest URL** that gets to the form: include project / account IDs as path or query params. Useful starting points (verify they still resolve; consoles move things):
  - GCP OAuth clients: `https://console.cloud.google.com/auth/clients?project=<project-id>` (create: `/auth/clients/create?project=…`); consent screen / branding: `/auth/branding?project=…`; APIs: `/apis/library/<api>.googleapis.com?project=…`
  - Cloudflare user API tokens: `https://dash.cloudflare.com/profile/api-tokens`; account-owned tokens: `https://dash.cloudflare.com/<account-id>/api-tokens`; R2 tokens: `https://dash.cloudflare.com/<account-id>/r2/api-tokens`
  - GitHub classic PAT (prefillable): `https://github.com/settings/tokens/new?description=<d>&scopes=<s1>,<s2>`; OAuth app: `https://github.com/settings/applications/new` (org: `/organizations/<org>/settings/applications/new`)
- **If you land on a login / account-chooser / 2FA page: stop.** Never type passwords or codes. Tell the user to sign in in that tab, then say "continue" (or re-run `/tee`).

## 4. Fill everything up to the final commit step

- Use `form_input` (by ref, from `read_page` / `find`) for text — Vimium is active, so raw `computer type` keystrokes are unreliable (see CLAUDE.md "Vimium is installed"). Click selects / checkboxes / radio buttons / "Add item" buttons as needed.
- Walk multi-step wizards (e.g. CF token: template → permissions → resources → "Continue to summary") as long as each "Next"/"Continue" only advances the wizard and commits nothing. When unsure whether a button commits, treat it as committing.
- Screenshot after each major step to confirm values landed (dropdowns and permission pickers often silently ignore input).
- If something in the form contradicts the plan (scope not offered, name already taken, quota hit), stop and report rather than improvising a different config.

## 5. Stop before anything irreversible

Do **not** click the final Create / Save / Confirm / Submit / Grant / Delete, and do not:
- accept terms or consent screens, or grant OAuth / SSO permissions
- enter secrets, passwords, card numbers, or 2FA codes
- delete or rotate existing credentials/resources, or change billing

Leave the tab on the page with that button visible (scroll it into view).

## 6. Hand off

Reply with:
- **Tab**: page title + URL, and the profile/email it's in.
- **Filled**: a compact checklist of what's set (name, IDs, URIs, each permission/scope + resource scoping, expiry).
- **Your move**: exactly which button(s) to review and click, plus any fields you deliberately left for them (and why).
- **After**: what the result will show and where it goes. If it reveals a secret (client secret, API token), tell them where to put it directly — the exact `wrangler secret put …` / `.envrc` line / secret-manager command for them to run — rather than pasting it into chat. Non-secret outputs (client ID, token ID) are fine to paste or for you to read off the page.

Then stop and wait. When they say done, you may re-read the tab (`read_page` / screenshot) to confirm the result and pick up non-secret values, then continue whatever work the task unblocked.

## Notes

- One `/tee` = one task. If the original ask had several console steps (e.g. enable an API, then create a client), do them in order, stopping at each commit point; on "done", continue to the next and hand off again.
- Never close the tab — it's the user's to finish.
