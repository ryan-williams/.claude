Define one or more abbreviations in CLAUDE.md, matching the terse style of the existing list.

Usage:
- `/abbrev XX` — infer meaning from recent conversation, choose scope, write
- `/abbrev XX YY ZZ` — multiple at once (group on one line if semantically related; separate lines otherwise)
- `/abbrev XX = explicit expansion` — skip inference, use the provided meaning
- `/abbrev -p XX` / `/abbrev -g XX` — force project / global scope (override the default)

The user wants this to be low-friction: write directly when confident, only ask when truly ambiguous.

Steps:

1. **Resolve meaning**: For each abbreviation, infer the intended expansion from the recent conversation — what the user just said, the file/domain context, or the surrounding work. If two readings are equally plausible, ask which one. If the user supplied `XX = expansion`, skip inference.

2. **Choose scope** (default: global; switch to project when meaning is project-specific):
   - **Global** (`~/.claude/CLAUDE.md`) — anything that could plausibly be reused across projects (general dev/debug/git/web/ML concepts, workflow shorthand, common nouns).
   - **Project** (`./CLAUDE.md` in the current project root) — domain terms, codebase concepts, proper nouns, or feature names tied to *this* project.
   - If the abbrev already has a global definition (collision), prefer project scope and don't touch the global entry.
   - If the project has no `CLAUDE.md`, ask before creating one (don't auto-create).
   - `-p` / `-g` flags override these defaults.

3. **Detect collisions**: Before writing, search the target file (and the other-scope file) for an existing entry. Loose patterns: `^- *<ABBR>\b`, `^- *.* = .*<ABBR>\b` (catches aliases like `mb = mob = mobile`), and case variations. If found:
   - Same scope, same meaning → no-op, report.
   - Same scope, different meaning → ask: replace, add as alias, or pick a longer abbrev.
   - Different scope → fine, just add (note the global entry exists, since the user said context-disambiguated collisions are acceptable).

4. **Write in matching style**:
   - Format: `- XX = expansion` (default; preserve user's case as typed — don't auto-uppercase or lowercase)
   - Some older entries use `:` instead of `=` (e.g. `WT:`, `UCs:`); for new entries use `=`.
   - Optional parenthetical for clarification: `XX = expansion (a.k.a. ...)`, `XX = expansion (context note)`
   - Multi-sentence explanation only when meaning is non-obvious or has important context (BC, IDP, OA, TFFP-style); otherwise keep it one line.
   - Aliases collapse onto one line with `=`: `mb = mob = mobile`, `n12e = NAI = NI = noninteractive`
   - Closely-related abbrevs from one invocation go on one line with commas + shared parenthetical: `CB = checkbox, RB = radio button, TB = text box (form input elements)`
   - Special encoding: `r13y = reproducibility`, `t10n = tokenization`, `n12e = noninteractive` — number = count of chars between first and last letter (i18n-style).

5. **Pick insertion point**:
   - Look for a semantically related neighbor in the existing list (a Git abbrev near `WT`/`UCs`/`SCs`; an ML abbrev near `LF`/`LR`/`SL`; a JS/web abbrev under the nested `In JS / web projects:` block).
   - Otherwise, append near the end of the flat list, before the closing "I also use ad hoc single-capital-letter abbreviations…" line.
   - When extending a multi-abbrev one-liner (e.g. user runs `/abbrev RG2` and `RG = regenerate` exists), consider rewriting the line as a multi-abbrev group if the new term shares the parenthetical/context.

6. **Report**: Print the inserted line(s), the file path, and (if a collision was detected) the conflict. Don't commit unless asked — the user will run `/c` separately.

Examples (from the existing list, for style reference):
- Single, no context: `- WB = wandb = Weights & Biases`
- With short parenthetical: `- AR = aspect ratio (a.k.a. "dims" for "dimensions")`
- Multi-sentence (non-obvious meaning): `- BC = backwards-compatibility (a.k.a. back-compat). Often I'm working on code that I've not pushed anywhere, and BC concerns would only have to do with other checkpoints in my current feature branch...`
- Multi-abbrev one-liner with shared parenthetical: `- CB = checkbox, RB = radio button, TB = text box (form input elements)`
- Numbered/encoded: `- r13y = reproducibility`
- Sub-bullet with overflow context: `- DS = downstream, US = upstream (for dependencies, data flow, etc.)` followed by `  - Sometimes, DS = dataset.`
