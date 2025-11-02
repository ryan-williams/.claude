# Claude Code Configuration

Personal [Claude Code] configuration and custom commands.

## Overview

This repository contains my global Claude Code settings, including:

- **`CLAUDE.md`**: Global instructions that Claude Code reads in every session
- **`commands/`**: Custom slash commands for common workflows

## Custom Commands

- **`/amend`**: Amend HEAD with uncommitted changes and rewrite the commit message
  - `/amend preserve` - Incorporate manual edits to the existing commit message
  - `/amend <context>` - Use additional context when drafting the message
- **`/docs`**: Review and update documentation files
  - `/docs <path>` - Focus on specific files or directories
- **`/commit`**: Analyze and commit changes
  - `/commit` - Commit in current directory
  - `/commit <path>` - Commit in a different repository

## Configuration Highlights

Key preferences documented in `CLAUDE.md`:

- **Git**: Use `git add -u` (not `-A`), avoid `git clean`, backticks for code symbols in commit messages
- **Python**: Multi-version venv system with `uv` and `direnv`, direct tool invocation without `uv run` prefixes
- **Coding style**: Direct imports, trailing commas, explicit error handling
- **Markdown**: Footer-style link definitions

## Setup

This is my `~/.claude` directory. To use similar configurations:

1. Create custom slash commands in `.claude/commands/*.md`
2. Add global instructions to `.claude/CLAUDE.md`
3. See [Claude Code documentation] for more details

[Claude Code]: https://claude.com/claude-code
[Claude Code documentation]: https://docs.claude.com/docs/claude-code
