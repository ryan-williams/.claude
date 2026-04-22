r"""Auto-approve engine: parse shell commands and match against YAML rules.

This module contains the core logic for the auto-approve hook. It can be
imported directly for testing, or used by the hook script.

See auto-approve-bash for the full docstring with safety analysis.
"""

from pathlib import Path
import re
import shlex
import yaml


# ── Token matchers ───────────────────────────────────────────────

class Literal:
    __slots__ = ("text",)
    def __init__(self, text):
        self.text = text
    def matches(self, token):
        return token == self.text

class AnyToken:
    def matches(self, _token):
        return True

class Alternation:
    __slots__ = ("options",)
    def __init__(self, options):
        self.options = frozenset(options)
    def matches(self, token):
        return token in self.options

class GlobPattern:
    """Matches one token against a glob pattern (* = .*)."""
    __slots__ = ("regex",)
    def __init__(self, pattern):
        escaped = re.escape(pattern).replace(r"\*", ".*")
        self.regex = re.compile(f"^{escaped}$")
    def matches(self, token):
        return bool(self.regex.match(token))


# Sentinel for end-of-pattern anchor
END_ANCHOR = object()


def parse_pattern(pattern_str: str) -> list:
    """Parse a pattern string into a list of token matchers."""
    matchers = []
    i = 0
    n = len(pattern_str)

    while i < n:
        while i < n and pattern_str[i] == " ":
            i += 1
        if i >= n:
            break

        c = pattern_str[i]

        if c == "$" and i == n - 1:
            matchers.append(END_ANCHOR)
            i += 1
        elif c == "(":
            j = pattern_str.find(")", i + 1)
            if j == -1:
                matchers.append(Literal(pattern_str[i:]))
                break
            options = pattern_str[i + 1 : j].split("|")
            matchers.append(Alternation(options))
            i = j + 1
        elif c in ('"', "'"):
            quote = c
            j = i + 1
            while j < n and pattern_str[j] != quote:
                if pattern_str[j] == "\\" and j + 1 < n:
                    j += 2
                else:
                    j += 1
            inner = pattern_str[i + 1 : j]
            if "*" in inner:
                matchers.append(GlobPattern(inner))
            else:
                matchers.append(Literal(inner))
            i = j + 1
        else:
            j = i
            while j < n and pattern_str[j] != " ":
                j += 1
            token = pattern_str[i:j]
            if token == "*":
                matchers.append(AnyToken())
            elif "*" in token:
                matchers.append(GlobPattern(token))
            else:
                matchers.append(Literal(token))
            i = j

    return matchers


def match_tokens(matchers: list, tokens: list[str]) -> bool:
    """Match parsed matchers against shlex-parsed tokens.

    Prefix matching by default. END_ANCHOR requires exact length.
    """
    exact = matchers and matchers[-1] is END_ANCHOR
    if exact:
        matchers = matchers[:-1]

    if len(tokens) < len(matchers):
        return False
    if exact and len(tokens) != len(matchers):
        return False

    for matcher, token in zip(matchers, tokens):
        if not matcher.matches(token):
            return False
    return True


def shlex_split_safe(command: str) -> list[str] | None:
    """shlex.split with fallback for malformed input."""
    try:
        return shlex.split(command)
    except ValueError:
        return None


# ── Shell pipeline splitting ─────────────────────────────────────

def _reassemble_compounds(segments: list[str]) -> list[str]:
    """Reassemble shell compound commands split across segments.

    Handles for/do/done, while/do/done, until/do/done, if/then/fi,
    case/in/esac.
    """
    OPENERS = {"for", "while", "until", "if", "case"}
    CLOSERS = {"done": {"for", "while", "until"}, "fi": {"if"}, "esac": {"case"}}

    result = []
    compound_parts: list[str] = []
    depth = 0
    opener_stack: list[str] = []

    for seg in segments:
        first_word = seg.split()[0] if seg.split() else ""
        base_word = first_word

        if depth == 0 and base_word in OPENERS:
            depth += 1
            opener_stack.append(base_word)
            compound_parts.append(seg)
        elif depth > 0:
            compound_parts.append(seg)
            if base_word in OPENERS:
                depth += 1
                opener_stack.append(base_word)
            last_word = seg.rstrip().split()[-1] if seg.split() else ""
            if last_word in CLOSERS:
                matching = CLOSERS[last_word]
                if opener_stack and opener_stack[-1] in matching:
                    depth -= 1
                    opener_stack.pop()
            if depth == 0:
                result.append("; ".join(compound_parts))
                compound_parts = []
        else:
            result.append(seg)

    if compound_parts:
        result.append("; ".join(compound_parts))

    return result


def split_shell_commands(command: str) -> list[str]:
    """Split a shell command on unquoted |, &&, ||, ;, &, \\n operators.

    Respects single quotes, double quotes, $() / `` substitutions,
    backslash escapes, and shell compound commands (for/done, if/fi, etc.).
    """
    segments = []
    current: list[str] = []
    i = 0
    n = len(command)

    while i < n:
        c = command[i]

        if c == "'":
            j = command.find("'", i + 1)
            if j == -1:
                current.append(command[i:])
                i = n
            else:
                current.append(command[i : j + 1])
                i = j + 1
        elif c == '"':
            j = i + 1
            while j < n:
                if command[j] == "\\" and j + 1 < n:
                    j += 2
                elif command[j] == '"':
                    break
                else:
                    j += 1
            current.append(command[i : j + 1])
            i = j + 1
        elif c == "$" and i + 1 < n and command[i + 1] == "(":
            depth = 1
            j = i + 2
            while j < n and depth > 0:
                if command[j] == "\\" and j + 1 < n:
                    j += 2
                    continue
                if command[j] == "(":
                    depth += 1
                elif command[j] == ")":
                    depth -= 1
                j += 1
            current.append(command[i:j])
            i = j
        elif c == "`":
            j = command.find("`", i + 1)
            if j == -1:
                current.append(command[i:])
                i = n
            else:
                current.append(command[i : j + 1])
                i = j + 1
        elif c == "\\" and i + 1 < n:
            if command[i + 1] == "\n":
                i += 2
            else:
                current.append(command[i : i + 2])
                i += 2
        elif c == "|" and i + 1 < n and command[i + 1] == "|":
            seg = "".join(current).strip()
            if seg:
                segments.append(seg)
            current = []
            i += 2
        elif c == "|":
            seg = "".join(current).strip()
            if seg:
                segments.append(seg)
            current = []
            i += 1
        elif c == "&" and i + 1 < n and command[i + 1] == "&":
            seg = "".join(current).strip()
            if seg:
                segments.append(seg)
            current = []
            i += 2
        elif c == "&":
            cur_str = "".join(current)
            if cur_str and cur_str[-1] == ">" or (len(cur_str) >= 2 and cur_str[-2].isdigit() and cur_str[-1] == ">"):
                current.append(c)
                i += 1
            else:
                seg = cur_str.strip()
                if seg:
                    segments.append(seg)
                current = []
                i += 1
        elif c in (";", "\n"):
            seg = "".join(current).strip()
            if seg:
                segments.append(seg)
            current = []
            i += 1
        else:
            current.append(c)
            i += 1

    seg = "".join(current).strip()
    if seg:
        segments.append(seg)
    return _reassemble_compounds(segments)


# ── Rule loading and matching ────────────────────────────────────

def _load_yaml(path: Path) -> dict:
    """Load and parse a YAML spec file. Returns empty dict on failure."""
    if not path.is_file():
        return {}
    try:
        data = yaml.safe_load(path.read_text())
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def load_rules(path: Path) -> list[dict]:
    """Load main rules from a YAML spec file."""
    return _load_yaml(path).get("rules", [])


def load_ssh_rules(path: Path) -> list[dict]:
    """Load SSH-specific rules from a YAML spec file."""
    return _load_yaml(path).get("ssh-rules", [])


# Commands that wrap another command. Each maps to how many args to skip
# after the wrapper keyword before the wrapped command begins.
# None = skip flags until a non-flag token, then skip that too if it's an arg.
_WRAPPER_CMDS = {
    "nohup": 0,       # nohup cmd args...
    "time": 0,         # time cmd args...
    "nice": None,      # nice [-n N] cmd args...
    "ionice": None,    # ionice [-c N] [-n N] cmd args...
    "timeout": 1,      # timeout DURATION cmd args...
    "strace": None,    # strace [-flags] cmd args...
    "ltrace": None,    # ltrace [-flags] cmd args...
}


def _strip_wrappers(cmd: str) -> str:
    """Strip wrapper commands (nohup, timeout, time, etc.) to get the inner command.

    Operates on the raw string to preserve redirects and other shell syntax
    that shlex.join would mangle.
    """
    stripped = cmd
    changed = True
    while changed:
        changed = False
        tokens = shlex_split_safe(stripped)
        if not tokens or tokens[0] not in _WRAPPER_CMDS:
            break

        skip_mode = _WRAPPER_CMDS[tokens[0]]
        # Count how many tokens to skip
        skip_count = 1  # the wrapper itself

        if skip_mode is None:
            # Skip flags and their args
            i = 1
            while i < len(tokens) and tokens[i].startswith("-"):
                i += 1
                if i < len(tokens) and not tokens[i].startswith("-"):
                    i += 1
            skip_count = i
        elif isinstance(skip_mode, int):
            skip_count = 1 + skip_mode

        # Find the position in the raw string where the inner command starts
        # by finding each skipped token and advancing past it
        pos = 0
        for _ in range(skip_count):
            # Skip whitespace
            while pos < len(stripped) and stripped[pos] == " ":
                pos += 1
            if pos >= len(stripped):
                return cmd
            # Skip the token (could be quoted)
            if stripped[pos] in ('"', "'"):
                quote = stripped[pos]
                pos += 1
                while pos < len(stripped) and stripped[pos] != quote:
                    if stripped[pos] == "\\" and pos + 1 < len(stripped):
                        pos += 2
                    else:
                        pos += 1
                pos += 1  # closing quote
            else:
                while pos < len(stripped) and stripped[pos] != " ":
                    pos += 1

        result = stripped[pos:].strip()
        if result and result != stripped:
            stripped = result
            changed = True

    return stripped


def _unwrap_command(command: str) -> tuple[str, str | None]:
    """Unwrap wrappers, assignments, SSH, etc. to get the actual command.

    Returns (unwrapped_command, ssh_host_or_None).
    """
    cmd = _strip_wrappers(command)

    m = re.match(r'^(export|local|declare|readonly|typeset)\s+', cmd)
    if m:
        cmd = cmd[m.end():]

    m = re.match(r'^[A-Za-z_]\w*=\$\((.+)\)\s*$', cmd)
    if m:
        return m.group(1), None
    if re.match(r'^[A-Za-z_]\w*=\S*\s*$', cmd):
        return "", None
    m = re.match(r'^[A-Za-z_]\w*=\S*\s+(.+)$', cmd)
    if m:
        cmd = m.group(1)

    if cmd.startswith("ssh "):
        tokens = shlex_split_safe(cmd)
        if tokens and tokens[0] == "ssh":
            opts_with_args = {"-o", "-p", "-i", "-l", "-J", "-F", "-S", "-W", "-b", "-c", "-D", "-E", "-L", "-R"}
            i = 1
            while i < len(tokens):
                if tokens[i].startswith("-"):
                    if tokens[i] in opts_with_args and i + 1 < len(tokens):
                        i += 2
                    else:
                        i += 1
                else:
                    break
            if i < len(tokens):
                host = tokens[i]
                remote_cmd = tokens[i + 1:] if i + 1 < len(tokens) else []
                if remote_cmd:
                    if len(remote_cmd) == 1:
                        return remote_cmd[0], host
                    else:
                        return " ".join(remote_cmd), host

    return cmd, None


def _match_trie(tokens: list[str], trie: dict) -> bool:
    """Match tokens against a trie (dict) structure."""
    for prefix_str, subtree in trie.items():
        prefix_matchers = parse_pattern(prefix_str)
        if len(tokens) < len(prefix_matchers):
            continue
        if not all(m.matches(t) for m, t in zip(prefix_matchers, tokens)):
            continue
        remaining = tokens[len(prefix_matchers):]

        if subtree is None or subtree is True:
            return True
        elif isinstance(subtree, list):
            if not remaining:
                return True
            for entry in subtree:
                if not isinstance(entry, str):
                    continue
                entry_matchers = parse_pattern(entry)
                if not entry_matchers or len(remaining) < len(entry_matchers):
                    continue
                if all(m.matches(t) for m, t in zip(entry_matchers, remaining)):
                    return True
        elif isinstance(subtree, dict):
            if _match_trie(remaining, subtree):
                return True
    return False


def match_rules(
    command: str,
    rules: list[dict],
    ssh_rules: list[dict] | None = None,
) -> str | None:
    """Evaluate rules against a single command segment.

    Returns 'allow', 'deny', 'ask', or None.
    """
    command, ssh_host = _unwrap_command(command)
    if not command:
        return "allow"

    if ssh_host is not None:
        if ssh_rules is None:
            return None
        return evaluate_command(command, ssh_rules=ssh_rules, rules=ssh_rules)

    tokens = shlex_split_safe(command)

    for rule in rules:
        if not isinstance(rule, dict):
            continue

        for action_key in ("allow", "deny", "ask", "allow-regex", "deny-regex", "ask-regex"):
            pattern = rule.get(action_key)
            if pattern is None:
                continue

            action = action_key.split("-")[0]

            if action_key.endswith("-regex"):
                try:
                    if re.search(pattern, command):
                        return action
                except re.error:
                    pass
            elif isinstance(pattern, list):
                if tokens is None:
                    continue
                for pat in pattern:
                    try:
                        matchers = parse_pattern(str(pat))
                        if match_tokens(matchers, tokens):
                            return action
                    except Exception:
                        pass
            elif isinstance(pattern, dict):
                if tokens is None:
                    continue
                try:
                    if _match_trie(tokens, pattern):
                        return action
                except Exception:
                    pass
            else:
                if tokens is None:
                    continue
                try:
                    matchers = parse_pattern(str(pattern))
                    if match_tokens(matchers, tokens):
                        return action
                except Exception:
                    pass

    return None


def _extract_compound_body(segment: str) -> list[str] | None:
    """Extract body commands from a compound statement."""
    first_word = segment.split()[0] if segment.split() else ""
    if first_word not in ("for", "while", "until", "if", "case"):
        return None

    parts = [p.strip() for p in segment.split(";") if p.strip()]

    body = []
    BODY_STARTERS = ("do", "then", "else")
    CLOSERS = ("done", "fi", "esac")
    in_body = False

    for part in parts:
        words = part.split()
        if not words:
            continue
        fw = words[0]

        if fw in BODY_STARTERS:
            rest = part[len(fw):].strip()
            if rest and rest not in CLOSERS:
                body.append(rest)
            in_body = True
        elif fw in CLOSERS or words[-1] in CLOSERS:
            in_body = False
        elif in_body:
            body.append(part)

    return body if body else None


def evaluate_command(
    command: str,
    rules: list[dict],
    ssh_rules: list[dict] | None = None,
) -> str | None:
    """Evaluate a full command, splitting pipelines/compounds.

    ALL segments must be 'allow' → allow.
    ANY segment 'deny' → deny.
    ANY segment 'ask' or None → None (normal prompt).
    """
    segments = split_shell_commands(command)
    segments = [s for s in segments if s and not s.lstrip().startswith("#")]
    if not segments:
        return None

    if len(segments) == 1:
        body = _extract_compound_body(segments[0])
        if body:
            segments = body
        else:
            decision = match_rules(segments[0], rules, ssh_rules)
            return None if decision == "ask" else decision

    expanded = []
    for seg in segments:
        body = _extract_compound_body(seg)
        if body:
            expanded.extend(body)
        else:
            expanded.append(seg)

    has_ask = False
    for seg in expanded:
        decision = match_rules(seg, rules, ssh_rules)
        if decision == "deny":
            return "deny"
        if decision in (None, "ask"):
            has_ask = True

    return None if has_ask else "allow"
