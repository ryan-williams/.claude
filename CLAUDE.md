## General Claude Instructions
- Don't tell me "You're absolutely right!" or similar. My suggestions will sometimes be purposely incorrect, to see if you're actually following / thinking things through. You **must** correct me when I say inaccurate things, and call out when my suggestions/ideas are not most advisable or idiomatic.
- Ensure lines don't end with trailing whitespace (in code and other text, where linters would normally check for fix this).
- Ensure text files end with a single newline character.

## Git Usage Conventions
- Avoid `git add -A`. I often have persistent untracked files I don't want to commit. `git add -u` (and `git add`ing specific untracked files, when intended) is a better method.
- Don't `git commit` changes unless I've told you to (on a per-session basis).
- Don't write to global `/tmp` dirs, use local `tmp/...` folders instead.
- If I link to or mention a GitHub Actions job / URL, read its logs using `gh` to understand what happened.
- My Git remote names are usually single chars corresponding to the GitHub org of the repo (or a given fork); I mostly avoid `origin`, and have `git config --global clone.defaultRemoteName u` (for "upstream").
- We're usually in a Git-tracked directory, so you don't need to copy files to "v2" versions to make big changes.

## Python Style / Conventions
- Err on the side of `import`ing members directly (e.g. `from click import option`) as opposed to including module-name boilerplate in code (e.g. `click.option`)
- Use trailing commas in lists of arguments, imported names, etc.
- Unexpected/Error states should `raise`; don't suppress errors (with `try`/`except` of `if`/`else`) unless they are legitimate states where both branches can be explained as valid/expected code paths (in which case they should both be documented as such).
- Scripts should generally use a `uv` shebang line, and include any required dependencies:
  - I use `click` for CLIs
    - `@option(...)`s should generally be on one line; don't put the `help="..."` string on the next line from the `@option` decorator.
    - Put `@argument`s after `@option`s.
  - `utz` is a library I maintain, with lots of helpers I often use in scripts (e.g. `utz.proc` wrappers around `subprocess`, `err = partial(print, file=sys.stderr)` for error printing, etc.)
    - `utz.cli.{opt,arg,flag,cmd,...}` are aliases around `click` decorators, that I prefer to use (`flag` in particular replaces `@click.option(..., is_flag=True)`). There are other similar `utz.cli` helpers you can use as well.
  - Log statements should go to stderr (using `err`); use stdout for primary output (e.g. if the script is used in a pipe).
  - Function and method args should have type annotations, and go on separate lines once there's ≥3 of them.
