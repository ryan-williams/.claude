## General Claude Instructions
- Don't say "You're absolutely right!" or similar. My suggestions will sometimes be purposely incorrect, to see if you're actually following and thinking things through. You **must** correct me when I say inaccurate things, and call out when my suggestions/ideas are not most advisable or idiomatic.
- Ensure lines don't end with trailing whitespace (in code and other text, where linters would normally check for and fix this).
- Ensure text files end with a single newline character.
- Don't leave "tombstone" comments about code you remove.
- Pipe long-running / large-output cmds through `tee tmp/<descriptive name>`, before piping on to `head` or `tail`. That way, in case `head` or `tail` isn't enough, you can see more info, without re-running the cmd.
  - `curl`s should write their outputs to a local file, then read from there (more like typical `wget` usage). You shouldn't have to `curl` the same file twice in quick succession / if you're not expecting it to have changed.
- I'm usually on macOS or Linux (Ubuntu); assume a Unix-like environment, and use `\n`s (not `\r\n`s) in text files.
- When I want a Claude session in one project to make changes in another project, I will have a separate session run in that project. I avoid having multiple Claude sessions active in any given project/directory.
  - The main workflow I use for this is for the former session to write a "spec" `.md` file in the latter's directory, which can then be read and implemented by a session that lives there. 
  - You can write into `specs/` in the root dir of the target project; I'll generally `.git/info/exclude` that dir, or leave it untracked.  

## Acronyms / Shorthands
I use these acronyms and abbreviations:
- **WT**: Git worktree
- **UCs**: Uncommitted Changes (staged and unstaged)
- **SCs**: Staged Changes (Git index)
- **USCs**: UnStaged Changes
- **UFs**: Untracked Files (Git)
- **TP** / **FP** / **TN** / **FN**: True Positive / False Positive / True Negative / False Negative
- **BC** = backwards-compatibility (a.k.a. back-compat). Often I'm working on code that I've not pushed anywhere, and BC concerns would only have to do with other checkpoints in my current feature branch, where BC is not important, and is even negative-value (bc it adds needless code complexity). In such cases I might just say "forget BC" or similar.
- **FFR** = For Future Reference
- OA = Open Athena (https://www.openathena.ai/, https://github.com/open-athena); "a nonprofit that accelerates academia with capabilities from the AI frontier", company I work for.
- MD = metadata (or Markdown)
- SFs = significant figures / sig-figs
- RG = regenerate
- IDP = idempotent, IDPy = idempotency.
  - I'll often be referring to jobs which, when re-run, should either 1) realize they don't need to RG, and short-circuit, or 2) RG and produce byte-identical outputs. RGIP can specifically mean the latter.
- GH = GitHub, GL = GitLab, GHA = GitHub Actions
- In JS / web projects:
  - FE / BE = Frontend / Backend, BB = Bounding Box
  - LS / SS = `localStorage` / `sessionStorage`
  - LM / DM = Light Mode / Dark Mode (for theming)
  - vp / vh / vw = viewport, viewport height, viewport width
- In general SS can also mean "screenshot", and "cast" = "screencast" (screen recording).

I also use ad hoc single-capital-letter abbreviations, when it should be clear from context what noun (proper or otherwise) I'm referring to.

## Git Usage Conventions
- **Avoid `git add -A`**: I often have persistent untracked files and directories I don't want to commit. `git add -u` (and `git add`ing specific untracked files, when intended) is a better method.
- Similarly, **don't use `git clean -fd`** or similar; I often have untracked files/dirs that are important and I want to keep.
- Don't `git commit` changes unless I've told you to (on a per-session basis).
- Don't write to global `/tmp` dirs, use local/relative `tmp/...` subdirs instead.
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
- **Non-interactive rebase**: Use `g rni` (`git rebase-noninteractive`) to apply rebase plans from stdin without interactive editing. Useful for scripted rewording/reordering.

## Dotfiles / Bash
- [runsascoded/.rc] is cloned at `~/.rc`, containing scripts and `alias`es I use frequently, grouped into Git submodules ≈per tool or category, e.g.:
  - `~/.rc/git` is [ryan-williams/git-helpers], which defines lots of aliases beginning with `g`, e.g. `gco` (`git checkout`), `ga` (`git add`), etc.
    - If I reference cmds beginning with `g`, it's likely defined there; look them up to understand what they do.
  - `~/.rc/parquet` contains useful scripts, many are wrappers around https://github.com/jupiter/parquet2json: `pqc` ("cat"), `pqn` (num rows), `pqs` (schema), `pqa` ("all": includes MD5, schema, num rows, and 3 head and tail rows), `pqm` (metadata), etc.
  - `~/.rc/py` contains helpers for Python (including venv and `uv` mgmt, see below)
- On my laptop, `$c` points at `~/c`: a root dir where I clone most source code repos.
  - On EC2 nodes I usually just clone a few repos relevant to a specific project directly under `~/`.

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
- **Testing**: Don't use vague membership assertions like `assert expected_substring in actual_string` or `assert elem in array`. Use precise matching instead:
  - Exact string/array equality
  - Match arrays of string lines
  - Robust regex matching
  - Specific element-by-element assertions
  - Other precise assertions that clearly document expected values
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

## JavaScript / TypeScript / Node.js / Web Development
- Use `pnpm` for package management, not `npm` (e.g., `pnpm install`, `pnpm add <package>`)
- I usually use Vite, TS, React, and SASS. Vite projects should have script `    "clean": "rm -rf node_modules/.vite dist"`
- I ≈always want MUI Tooltips, not browser-native tooltips. The latter take too long to appear, and are too small/flat/unstyleable/plain.
- Each project should default its dev (or built) servers to a hopefully-unique, unused port (not Vite's default 5173, slidev's 3030, http-server's 8080, etc.) to avoid conflicts when running multiple projects simultaneously on a given host.
  - A nice trick is to hash the project name, and mod that into an eligible range of port numbers.
- Check whether there's a server running on the desired port before starting any server and, if so, warn and prompt me.
  - Sometimes this will be a dev server I am running in the project, meaning you don't have to boot your own.

My `vite.config.ts` will usually do something like:

```ts
const allowedHosts = process.env.VITE_ALLOWED_HOSTS?.split(',') ?? []

export default defineConfig({
  server: {
    port: 3201,  // ≈unique to project
    host: true,
    allowedHosts,
  },
})
```

so that my tailnet can access dev servers (via `$VITE_ALLOWED_HOSTS`, which my dotfiles set).

### Frequently Used JS/TS Tools and Libraries
`$js` (`~/c/js`) is a root dir for JS/TS projects I maintain, most of which live under https://gitlab.com/runsascoded/js.

Several tools I often use while developing other applications and libraries:

- `npm-dist` (https://github.com/runsascoded/npm-dist / https://gitlab.com/runsascoded/js/npm-dist): Git{Hu,La}b Action to build and publish "dist" branches for npm packages, which can be directly added (by SHA or branch name, but I always prefer SHA) in downstream `package.json`s (or via `pds gh <name>`, per below).
- [`pnpm-dep-source`] (a.k.a. `pds`; https://github.com/runsascoded/pnpm-dep-source): manage dependencies that I may be developing locally in tandem with local projects that use them:
  - `pds init <path>`: declare `<path>` as a `pds`-managed dependency in a given project
  - `pds [l|local] <name>`: point current project at local build of `<name>`
    - Note: `<name>` can be any unique substring match, here and in other cmds below
    - Manages settings in 2-3 places, including `pnpm-workspace.yaml`, that are necessary for "hot-reloading" of local dependencies to work.
  - `pds [gh|gl] <name>`: point at a recent Git{Hu,La}b "dist"-branch build
  - `pds [n|npm] <name> [version]`: point at latest published npm version
  - `pds` stores its config state in a `.pnpm-dep-source.json` file, in each web project's root dir.
- [`scrns`] (https://gitlab.com/runsascoded/js/scrns): screenshot automation tool, frequently used for preview images in `README.md`s, `og:image`s, etc.

[`pnpm-dep-source`]: https://www.npmjs.com/package/pnpm-dep-source
[`scrns`]: https://www.npmjs.com/package/scrns

And a few libraries I often use in JS/TS apps:
- [`use-kbd`] (https://github.com/runsascoded/use-kbd): Omnibars, editable hotkeys, search, and keyboard-navigation for React apps.
- [`use-prms`] (https://github.com/runsascoded/use-prms): React hooks for managing URL query parameters with type-safe encoding/decoding
- [`@rdub/base`] (https://gitlab.com/runsascoded/js/base): helpers and convenience imports arguably missing from stdlib (e.g. for Object, Array, Math, …; also some React)

[`use-kbd`]: https://www.npmjs.com/package/use-kbd
[`use-prms`]: https://www.npmjs.com/package/use-prms
[`@rdub/base`]: https://www.npmjs.com/package/@rdub/base

## Markdown
- Define links' hrefs in the "footer", so that the inline links only require writing e.g. `[anchor text]` or `[long anchor text][short name]`, not full URLs.

## Diffs
`dffs` (https://github.com/runsascoded/dffs) should be `pipx install`'d and globally accessible (and also cloned at `~/c/dffs`), and exposes CLIs:
- `diff-x` ("Diff two files after running them through a pipeline of other commands"), a.k.a. `dx*`
- `git-diff-x` ("Diff files at two commits, or one commit and the current worktree, after applying an optional command pipeline"), a.k.a. `gdx*`
- `comm-x` ("Select or reject lines common to two input streams, after running each through a pipeline of other commands.")
