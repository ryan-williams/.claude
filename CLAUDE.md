## General Claude Instructions
- Don't say "You're absolutely right!" or similar. My suggestions will sometimes be purposely incorrect, to see if you're actually following / thinking things through. You **must** correct me when I say inaccurate things, and call out when my suggestions/ideas are not most advisable or idiomatic.
- Ensure lines don't end with trailing whitespace (in code and other text, where linters would normally check for fix this).
- Ensure text files end with a single newline character.
- Don't leave "tombstone" comments about things you remove.

## Git Usage Conventions
- **Avoid `git add -A`**: I often have persistent untracked files and directories I don't want to commit. `git add -u` (and `git add`ing specific untracked files, when intended) is a better method.
- Similarly, **don't use `git clean -fd`** or similar; I often have untracked files/dirs that are important and I want to keep.
- Don't `git commit` changes unless I've told you to (on a per-session basis).
- Don't write to global `/tmp` dirs, use local `tmp/...` subdirs instead.
- If I link to or mention a GitHub Actions job / URL, read its logs (using `gh run view --log`) to understand what happened.
- My Git remote names are usually single chars corresponding to the GitHub org of the repo (or a given fork); I avoid `origin`, and have `git config --global clone.defaultRemoteName u` (for "upstream").
- You're usually in a Git-tracked directory, so you don't need to copy files to "_v2", ".bak", or "_copy" versions when making big changes.
  - Use Git branches instead of `.bak` files or untracked copies of files, `_v2` suffixes, etc.

## Dotfiles
- [runsascoded/.rc] is cloned at `~/.rc`, containing scripts and `alias`es I use frequently, grouped into Git submodules ≈per tool or category.
- `~/.rc/git` is [ryan-williams/git-helpers], which defines lots of aliases beginning with `g`, e.g. `gco` (`git checkout`), `ga` (`git add`), etc.
  - If I reference cmds beginning with `g`, it's likely defined there; look them up to understand what they do.

[runsascoded/.rc]: https://github.com/runsascoded/.rc
[ryan-williams/git-helpers]: https://github.com/ryan-williams/git-helpers

## Python Style / Conventions
- `import` members directly (e.g. `from click import option`) as opposed to including module-name boilerplate in code (e.g. `click.option`)
- Use trailing commas in argument lists, multi-line imports, etc.
- Unexpected/Error states should `raise`; don't suppress errors (with `try`/`except` or `if`/`else`) unless they're legitimate states, where both branches can be explained as valid/expected code paths (in which case they should both be documented as such).
- Scripts should use a `uv run` shebang line, and include any required dependencies:
  - Use `click` for CLIs:
    - Each `@option(...)` and `@argument(...)` should be on one line; don't put the `help="..."` string on a separate line from the decorator.
    - Put `@argument`s after `@option`s (and order the corresponding `def` args similarly).
    - Give `@option`s a single-char short letter alias, before their longer, double-dashed name (e.g. `'-f', '--force', ...`). Declare them in alphabetical order (by single-char aliases, falling back to full names). Use upper-case single-char aliases for `--no-...` flags, disabling default-enabled behavior (e.g. `'-O', '--no-open', ...`).
  - I maintain `utz`, with many helpers I use in scripts, e.g.:
    - `utz.proc` (wrappers around `subprocess`)
    - `err = partial(print, file=sys.stderr)` for error printing
    - `utz.cli.{opt,arg,flag,cmd,...}` aliases around `click` decorators
      - `flag` replaces `@click.option(..., is_flag=True)`)
  - Log statements should go to stderr (using `err`); use stdout for primary / pipe-able / parse-able output.
  - Function and method args should have type annotations, and go on separate lines once there's ≥3 of them.

## Markdown
- Define links' hrefs in the "footer", so that the inline link only requires writing e.g. `[anchor text]` or `[long anchor text][short name]`.
