## General Claude Instructions
- Don't say "You're absolutely right!" or similar. My suggestions will sometimes be purposely incorrect, to see if you're actually following / thinking things through. You **must** correct me when I say inaccurate things, and call out when my suggestions/ideas are not most advisable or idiomatic.
- Ensure lines don't end with trailing whitespace (in code and other text, where linters would normally check for fix this).
- Ensure text files end with a single newline character.
- Don't leave "tombstone" comments about things you remove.
- Pipe long-running / large-output cmds through `tee tmp/<descriptive name>`, before piping on to `head` or `tail`. That way, in case `head` or `tail` isn't enough, you can see more info, without re-running the cmd.

## Acronyms / Shorthands
I use these acronyms and abbreviations:
- **WT**: Git worktree
- **UCs**: Uncommitted Changes (staged and unstaged)
- **SCs**: Staged Changes (Git index)
- **USCs**: UnStaged Changes
- **UFs**: Untracked Files (Git)

I also use single-capital letter abbreviations ad hoc when it should be clear from context what noun (proper or otherwise) I mean.

## Git Usage Conventions
- **Avoid `git add -A`**: I often have persistent untracked files and directories I don't want to commit. `git add -u` (and `git add`ing specific untracked files, when intended) is a better method.
- Similarly, **don't use `git clean -fd`** or similar; I often have untracked files/dirs that are important and I want to keep.
- Don't `git commit` changes unless I've told you to (on a per-session basis).
- Don't write to global `/tmp` dirs, use local `tmp/...` subdirs instead.
- If I link to or mention a GitHub Actions job / URL, read its logs (using `gh run view --log`) to understand what happened.
  - Save the logs to a local file, then read from there (so you don't have to fetch them more than once).
- My Git remote names are usually single chars corresponding to the GitHub org of the repo (or a given fork); I avoid `origin`, and have `git config --global clone.defaultRemoteName u` (for "upstream").
- You're usually in a Git-tracked directory, so you don't need to copy files to "_v2", ".bak", or "_copy" versions when making big changes.
  - Use Git branches instead of `.bak` files or untracked copies of files, `_v2` suffixes, etc.
- **User branches**: I use `gpu` (`git push-user-branch`) to push local branches to remote user namespaces
  - Example: `gpu` on local branch `feat` pushes to `u/rw/feat` (where `rw` is from `GIT_USER_BRANCH_PREFIX`)
  - Variants: `gpuf` (force), `gpun` (dry-run)
  - The script auto-detects the tracking remote or uses `-r <remote>` flag
- **Commit messages**: Use backticks around code symbols (functions, variables, file names, commands, etc.) in commit messages. GitHub renders these in PR/issue titles and bodies, making it clear what refers to code.

## Dotfiles
- [runsascoded/.rc] is cloned at `~/.rc`, containing scripts and `alias`es I use frequently, grouped into Git submodules ≈per tool or category.
- `~/.rc/git` is [ryan-williams/git-helpers], which defines lots of aliases beginning with `g`, e.g. `gco` (`git checkout`), `ga` (`git add`), etc.
  - If I reference cmds beginning with `g`, it's likely defined there; look them up to understand what they do.

[runsascoded/.rc]: https://github.com/runsascoded/.rc
[ryan-williams/git-helpers]: https://github.com/ryan-williams/git-helpers

## Python Environment Management
I use a multi-version venv system with `uv` and `direnv`, managed by `spd` and related commands from `~/.rc/py/`:

### Directory Structure
```
.venv/
  3.11.13/      # Actual venv for Python 3.11.13
  3.12.11/      # Actual venv for Python 3.12.11
  3.13.7/       # Actual venv for Python 3.13.7
  bin -> 3.13.7/bin         # Symlink to active version
  lib -> 3.13.7/lib
  include -> 3.13.7/include
  pyvenv.cfg -> 3.13.7/pyvenv.cfg
  current       # File containing "3.13.7"
  .lock         # Lock file
```

### Key Commands
- **`spd`** (`py_direnv_init`): Setup/repair Python project with direnv
  - Creates `.envrc` that sources `py-direnv-rc.sh`
  - Converts old-style flat `.venv/` to versioned structure
  - Auto-repairs existing `.envrc` files missing venv management
  - Runs `uv sync` for projects with `uv.lock`
  - Idempotent: safe to run multiple times
- **`vl`**: List available venvs (shows versions + active marker)
- **`vsw 3.12`** / **`vw 3.12`**: Switch to Python 3.12.x venv
- **`vc 3.11 3.12 3.13`**: Create venvs for specific Python versions
- **`pip`**: In UV projects, this is a wrapper around `uv pip`

### UV Integration
- `UV_PROJECT_ENVIRONMENT` and `VIRTUAL_ENV` are both set to `.venv` (the symlink)
- UV follows the symlink to the actual versioned venv
- `uv sync` installs into the active venv
- Use `uv sync --extra <name>` (or `uvse <name>`) to install optional dependency groups

### Invoking Python Tools
Since `direnv` activates the venv automatically, installed tools are directly available on `PATH`:
- Use `python`, `pip`, `pytest`, etc. directly (NOT `uv run python`, `uv run pytest`)
- `pip` is a wrapper around `uv pip` in UV projects
- Only use `uv run` for ad-hoc scripts with inline dependencies

### Common Workflow
```bash
cd my-project
spd              # Setup project (creates .envrc, .venv structure)
# direnv auto-activates on cd
vl               # List available Python versions
vsw 3.12         # Switch to Python 3.12 if needed
uv sync          # Sync dependencies
```

## Python Style / Conventions
- **Invoking scripts**: I have `.` on `$PATH` and Python scripts are typically executable (`+x`), so invoke them directly by name (not `./script.py` or `python script.py`). Use `which` to find them if needed.
- `import` members directly (e.g. `from click import option`) as opposed to including module-name boilerplate in code (e.g. `click.option`)
- Use trailing commas in argument lists, multi-line imports, etc.
- Unexpected/Error states should `raise`; don't suppress errors (with `try`/`except` or `if`/`else`) unless they're legitimate states, where both branches can be explained as valid/expected code paths (in which case they should both be documented as such).
- **Testing**: Don't use substring assertions like `assert expected_substring in actual_string`. Use precise matching instead:
  - Exact string equality
  - Match arrays of string lines
  - Robust regex matching
  - Other specific assertions
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

## JavaScript / Node.js
- Use `pnpm` for package management, not `npm` (e.g., `pnpm install`, `pnpm add <package>`)

## Markdown
- Define links' hrefs in the "footer", so that the inline link only requires writing e.g. `[anchor text]` or `[long anchor text][short name]`.
