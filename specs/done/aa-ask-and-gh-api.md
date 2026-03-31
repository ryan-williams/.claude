# Auto-approve: `ask` action + `gh api` implicit-POST vulnerability

## Problem 1: no `ask` action

The auto-approve hook has two actions: `allow` (auto-approve) and `deny` (hard block). There's no way to say "don't auto-approve this, but do prompt normally."

This matters when a broad `allow` rule exists and a narrower exception needs to fall through to the prompt:

```yaml
rules:
  - deny-regex: '^gh api .*(-X |--method )'  # intended: "just ask", actual: hard block
  - allow:
      gh api: ~   # auto-approve all gh api
```

The intent is: auto-approve read-only `gh api` calls, prompt for mutating ones. But `deny` hard-blocks them instead of prompting, so Claude can't run `gh api ... -X POST` even with user approval.

### Fix

Add an `ask` (or `skip`) action type:
- `allow`: auto-approve, stop matching
- `ask`: stop matching, fall through to normal permission prompt
- `deny`: hard block, never run

```yaml
rules:
  - ask-regex: '^gh api .*(-X |--method )'   # prompt, don't auto-approve
  - allow:
      gh api: ~   # auto-approve the rest (GETs)
```

Implementation: in the hook script, when an `ask` rule matches, exit with the "not covered" code (so Claude's normal permission prompt appears) instead of the "denied" code.

## Problem 2: `gh api` implicit POST bypass

`gh` infers the HTTP method from the flags:
- No data flags → GET
- `-f key=value`, `-F key=value`, `--input`, `--raw-field` → POST (implicit)
- `-X METHOD` / `--method METHOD` → explicit override

The current deny rule only catches `-X`/`--method`:

```yaml
- deny-regex: '^gh api .*(-X |--method )'
```

This means `gh api repos/.../comments -f body="..."` is a **POST** that bypasses the deny rule and gets auto-approved by `gh api: ~`. This is a vulnerability — mutating API calls are silently auto-approved.

### Fix

The deny (or, with fix #1, `ask`) rule should also match implicit-POST flags:

```yaml
- ask-regex: '^gh api .*(-X |--method |-f |-F |--input |--raw-field )'
```

This catches both explicit and implicit POST/PATCH/PUT/DELETE calls. Bare `gh api <endpoint>` (GET) still gets auto-approved.

## Summary

| Call | Old behavior | Desired | Implemented |
|---|---|---|---|
| `gh api repos/.../pulls` | allow | allow | allow |
| `gh api repos/.../comments -f body="..."` | **allow (bug)** | ask | ask |
| `gh api repos/.../comments -X POST -f body="..."` | **deny (too strict)** | ask | ask |
| `gh api -F key=@file.json /repos/foo` | **allow (bug)** | ask | ask |
| `gh api --input data.json /repos/foo` | **allow (bug)** | ask | ask |
| `gh api /repos/foo -X DELETE` | deny | ask | ask |

## Implementation notes

- Added `ask` / `ask-regex` action types to `auto-approve-bash`
- `ask` stops rule matching and falls through to normal permission prompt
- Changed `gh api` rule from `deny-regex` to `ask-regex`
- Expanded regex to catch implicit-POST flags: `-f`, `-F`, `--input`, `--raw-field`
