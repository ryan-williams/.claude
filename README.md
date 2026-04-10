# Claude Code Configuration

Personal [Claude Code] configuration: global instructions, custom commands, auto-approve hooks, and CLI helpers.

## Structure

| Path | Purpose |
|------|---------|
| `CLAUDE.md` | Global instructions loaded into every session |
| `commands/` | Custom slash commands |
| [`hooks/`](hooks/) | Auto-approve hook ([engine], [rules]) |
| `bin/` | CLI helper scripts |
| `settings.json` | Global permissions, hook config, plugins |
| `tests/` | Pytest tests for the hook engine |

## Auto-Approve (AA) System

A `PreToolUse` hook that auto-approves safe Bash commands based on YAML rules, so common read-only commands don't need manual approval:

- [`auto_approve.py`][engine]: engine
- [`auto-approve.yml`][rules]: my rules
- [Hooks docs][hooks]

**How it works:**
- Rules in [`hooks/auto-approve.yml`][rules] (global) and per-project `.claude/hooks/auto-approve.yml`
- Commands are split on `|`, `&&`, `||`, `;`, `&`, `\n` — ALL segments must pass
- Shell compound commands (`for`/`done`, `if`/`fi`) are decomposed into body commands
- Variable assignments (`VAR=$(cmd)`) and SSH (`ssh host "cmd"`) are unwrapped
- SSH commands are evaluated against a restricted `ssh-rules` subset

**Rule formats:**
```yaml
# String pattern (shlex-aware, prefix match)
- allow: git log

# List of patterns
- allow:
  - cat
  - head
  - tail

# Trie (prefix → allowed subcommands)
- allow:
    git: [branch, diff, log, status]
    git -C *: [branch, diff, log, status]

# Regex fallback
- allow-regex: '^curl (-s )?https?://localhost[:/]'
```

**Actions:** `allow` (auto-approve), `ask` (prompt normally), `deny` (hard block)

**YAML anchors** share read-only command lists between local and SSH rules.

## Commands

| Command | Description |
|---------|-------------|
| `/c [phases]` | Flexible Git workflow: `t`est, `c`ommit, `a`mend, `s`taged, `p`ush, `d`ispatch, `w`atch |
| `/commit` | Analyze and commit changes |
| `/commits` | Split changes into multiple logical commits |
| `/cs` | Commit staged changes only |
| `/amend` | Amend HEAD and rewrite commit message |
| `/resolve` (`/res`) | Resolve Git conflicts intelligently |
| `/w` | Watch most recent CI run (GitHub/GitLab) |
| `/pw` | Push, then watch CI |
| `/aa` | Propose auto-approve rules for last rejected command |
| `/aag` | Same as `/aa -g` (global rules) |
| `/bless <cmd>` | Analyze a command and propose AA rules |
| `/kill-server` (`/ks`) | Kill/restart dev server |
| `/spec` | Write a spec file for another project |
| `/specs` | Check for and implement pending specs |
| `/pdsd` | Retry after dependency update via `pds` |
| `/autosquash` (`/as`) | Autosquash uncommitted changes onto ancestor commits |
| `/docs` | Review and update documentation |

## CLI Helpers (`bin/`)

| Script | Description |
|--------|-------------|
| `aa-test` | Test if a command would be auto-approved |
| `bcg` | Shorthand for `bless-cmd -g` (global) |
| `bless-cmd` | Add a permission to Claude settings (`-g` for global) |
| `bless-repo` | Add read-only git permissions for a repo |
| `claude-cp` | Copy a Claude project config to a new path |
| `claude-mv` | Move a project directory and update Claude configs |
| `claude-settings-clean` | Clean up Claude settings files |

## Testing

```bash
pytest tests/ -v        # Run all tests
aa-test 'git log'       # Test a single command against AA rules
```

CI runs on push via [GitHub Actions](.github/workflows/test.yml).

[Claude Code]: https://claude.com/claude-code
[engine]: hooks/auto_approve.py
[rules]: hooks/auto-approve.yml
[YAML rules]: hooks/auto-approve.yml
[hooks]: https://code.claude.com/docs/en/hooks
