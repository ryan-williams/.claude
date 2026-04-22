"""Tests for the auto-approve engine."""

import sys
from pathlib import Path

import pytest

# Add hooks dir to path
sys.path.insert(0, str(Path(__file__).parent.parent / "hooks"))

from auto_approve import (
    Alternation,
    AnyToken,
    GlobPattern,
    Literal,
    _extract_compound_body,
    _match_trie,
    _reassemble_compounds,
    _strip_wrappers,
    _unwrap_command,
    evaluate_command,
    match_rules,
    match_tokens,
    parse_pattern,
    shlex_split_safe,
    split_shell_commands,
)


# ── Token matchers ───────────────────────────────────────────────

class TestLiteral:
    def test_exact_match(self):
        assert Literal("git").matches("git")

    def test_no_match(self):
        assert not Literal("git").matches("gит")
        assert not Literal("git").matches("git ")

class TestAnyToken:
    def test_matches_anything(self):
        assert AnyToken().matches("anything")
        assert AnyToken().matches("")

class TestAlternation:
    def test_match_in_set(self):
        a = Alternation(["branch", "diff", "log"])
        assert a.matches("branch")
        assert a.matches("diff")

    def test_no_match(self):
        a = Alternation(["branch", "diff", "log"])
        assert not a.matches("push")

class TestGlobPattern:
    def test_prefix_glob(self):
        g = GlobPattern("Print *")
        assert g.matches("Print :foo:bar")
        assert not g.matches("Set :foo bar")

    def test_suffix_glob(self):
        g = GlobPattern("http://localhost*")
        assert g.matches("http://localhost:3000")
        assert not g.matches("http://example.com")


# ── Pattern parsing ──────────────────────────────────────────────

class TestParsePattern:
    def test_literals(self):
        matchers = parse_pattern("git log")
        assert len(matchers) == 2
        assert isinstance(matchers[0], Literal)
        assert isinstance(matchers[1], Literal)

    def test_wildcard(self):
        matchers = parse_pattern("git -C * log")
        assert isinstance(matchers[2], AnyToken)

    def test_alternation(self):
        matchers = parse_pattern("git (branch|diff|log)")
        assert isinstance(matchers[1], Alternation)
        assert matchers[1].matches("branch")
        assert not matchers[1].matches("push")

    def test_quoted_glob(self):
        matchers = parse_pattern('"Print *"')
        assert len(matchers) == 1
        assert isinstance(matchers[0], GlobPattern)

    def test_end_anchor(self):
        from auto_approve import END_ANCHOR
        matchers = parse_pattern("echo hello $")
        assert matchers[-1] is END_ANCHOR


# ── Token matching ───────────────────────────────────────────────

class TestMatchTokens:
    def test_prefix_match(self):
        matchers = parse_pattern("git log")
        assert match_tokens(matchers, ["git", "log", "--oneline"])

    def test_exact_match_with_anchor(self):
        matchers = parse_pattern("echo hello $")
        assert match_tokens(matchers, ["echo", "hello"])
        assert not match_tokens(matchers, ["echo", "hello", "world"])

    def test_too_few_tokens(self):
        matchers = parse_pattern("git -C * log")
        assert not match_tokens(matchers, ["git", "-C"])

    def test_wildcard_matches_any_token(self):
        matchers = parse_pattern("git -C * log")
        assert match_tokens(matchers, ["git", "-C", "/some/path", "log"])
        assert match_tokens(matchers, ["git", "-C", "path with spaces", "log"])


# ── Pipeline splitting ──────────────────────────────────────────

class TestSplitShellCommands:
    def test_pipe(self):
        assert split_shell_commands("ls | head") == ["ls", "head"]

    def test_and(self):
        assert split_shell_commands("cmd1 && cmd2") == ["cmd1", "cmd2"]

    def test_or(self):
        assert split_shell_commands("cmd1 || cmd2") == ["cmd1", "cmd2"]

    def test_semicolon(self):
        assert split_shell_commands("cmd1; cmd2") == ["cmd1", "cmd2"]

    def test_newline(self):
        assert split_shell_commands("cmd1\ncmd2") == ["cmd1", "cmd2"]

    def test_background(self):
        assert split_shell_commands("cmd1 & cmd2") == ["cmd1", "cmd2"]

    def test_quoted_pipe_not_split(self):
        segs = split_shell_commands('git log --format="%H | %s"')
        assert len(segs) == 1

    def test_quoted_semicolon_not_split(self):
        segs = split_shell_commands("echo 'hello; world'")
        assert len(segs) == 1

    def test_command_substitution_not_split(self):
        segs = split_shell_commands("echo $(ls | head)")
        assert len(segs) == 1

    def test_backtick_not_split(self):
        segs = split_shell_commands("echo `ls | head`")
        assert len(segs) == 1

    def test_redirect_not_split(self):
        segs = split_shell_commands("cmd 2>&1")
        assert len(segs) == 1
        assert "2>&1" in segs[0]

    def test_line_continuation(self):
        segs = split_shell_commands("echo hello \\\nworld")
        assert len(segs) == 1

    def test_compound_for(self):
        segs = split_shell_commands("for x in 1 2; do echo $x; done")
        assert len(segs) == 1
        assert segs[0].startswith("for")

    def test_compound_with_surrounding(self):
        segs = split_shell_commands("echo start; for x in 1 2; do echo $x; done; echo end")
        assert len(segs) == 3
        assert segs[0] == "echo start"
        assert segs[1].startswith("for")
        assert segs[2] == "echo end"


# ── Compound body extraction ────────────────────────────────────

class TestExtractCompoundBody:
    def test_for_loop(self):
        body = _extract_compound_body("for x in 1 2; do echo $x; done")
        assert body == ["echo $x"]

    def test_for_loop_multiple_body(self):
        body = _extract_compound_body("for x in 1 2; do echo $x; cat file; done")
        assert body == ["echo $x", "cat file"]

    def test_not_compound(self):
        assert _extract_compound_body("echo hello") is None


# ── Wrapper stripping ───────────────────────────────────────────

class TestStripWrappers:
    def test_nohup(self):
        assert _strip_wrappers("nohup pnpm dev > /tmp/dev.log 2>&1") == "pnpm dev > /tmp/dev.log 2>&1"

    def test_timeout(self):
        assert _strip_wrappers("timeout 30 git log --oneline") == "git log --oneline"

    def test_time(self):
        assert _strip_wrappers("time ls -la") == "ls -la"

    def test_nice_with_flag(self):
        assert _strip_wrappers("nice -n 10 pnpm build") == "pnpm build"

    def test_no_wrapper(self):
        assert _strip_wrappers("git log") == "git log"

    def test_nested_wrappers(self):
        assert _strip_wrappers("nohup time pnpm build") == "pnpm build"

    def test_preserves_redirects(self):
        result = _strip_wrappers("nohup cmd > /tmp/out 2>&1")
        assert ">" in result
        assert "2>&1" in result


# ── Command unwrapping ──────────────────────────────────────────

class TestUnwrapCommand:
    def test_plain_command(self):
        assert _unwrap_command("ls -la") == ("ls -la", None)

    def test_assignment(self):
        assert _unwrap_command("VAR=hello") == ("", None)

    def test_export_assignment(self):
        assert _unwrap_command("export PATH=/usr/bin") == ("", None)

    def test_assignment_with_subshell(self):
        cmd, host = _unwrap_command("result=$(git log --oneline -1)")
        assert cmd == "git log --oneline -1"
        assert host is None

    def test_export_with_subshell(self):
        cmd, host = _unwrap_command("export FOO=$(echo bar)")
        assert cmd == "echo bar"
        assert host is None

    def test_env_prefix(self):
        cmd, host = _unwrap_command("VAR=value echo test")
        assert cmd == "echo test"
        assert host is None

    def test_ssh_simple(self):
        cmd, host = _unwrap_command('ssh myhost "ls -la /foo"')
        assert cmd == "ls -la /foo"
        assert host == "myhost"

    def test_ssh_with_options(self):
        cmd, host = _unwrap_command('ssh -o StrictHostKeyChecking=no myhost "cat /foo"')
        assert cmd == "cat /foo"
        assert host == "myhost"

    def test_ssh_with_user_at_host(self):
        cmd, host = _unwrap_command('ssh user@10.0.0.1 "head -5 /var/log/syslog"')
        assert cmd == "head -5 /var/log/syslog"
        assert host == "user@10.0.0.1"

    def test_ssh_unquoted_args(self):
        cmd, host = _unwrap_command("ssh myhost ls -la /foo")
        assert cmd == "ls -la /foo"
        assert host == "myhost"


# ── Trie matching ───────────────────────────────────────────────

class TestMatchTrie:
    def test_simple_trie(self):
        trie = {"git": ["branch", "diff", "log"]}
        assert _match_trie(["git", "log", "--oneline"], trie)
        assert not _match_trie(["git", "push"], trie)

    def test_wildcard_prefix(self):
        trie = {"git -C *": ["diff", "log"]}
        assert _match_trie(["git", "-C", "/path", "log"], trie)
        assert not _match_trie(["git", "-C", "/path", "push"], trie)

    def test_null_value_allows_anything(self):
        trie = {"gh api": None}
        assert _match_trie(["gh", "api", "/repos/foo"], trie)

    def test_no_match(self):
        trie = {"pnpm": ["build", "test"]}
        assert not _match_trie(["npm", "test"], trie)

    def test_multi_token_list_entry(self):
        """List entries can be multi-token patterns, not just single-token alternations."""
        trie = {"modal": ["volume list", "run scripts/*"]}
        assert _match_trie(["modal", "volume", "list"], trie)
        assert _match_trie(["modal", "run", "scripts/foo.py", "--steps", "20"], trie)
        assert not _match_trie(["modal", "deploy"], trie)
        assert not _match_trie(["modal", "volume", "delete"], trie)

    def test_multi_token_list_entry_with_glob(self):
        trie = {"modal": ["run scripts/*"]}
        assert _match_trie(["modal", "run", "scripts/train.py"], trie)
        assert not _match_trie(["modal", "run", "other/train.py"], trie)


# ── Rule matching ────────────────────────────────────────────────

class TestMatchRules:
    def test_string_pattern(self):
        rules = [{"allow": "git log"}]
        assert match_rules("git log --oneline", rules) == "allow"

    def test_list_pattern(self):
        rules = [{"allow": ["cat", "head", "tail"]}]
        assert match_rules("cat foo.txt", rules) == "allow"
        assert match_rules("rm foo.txt", rules) is None

    def test_trie_pattern(self):
        rules = [{"allow": {"git": ["branch", "diff", "log"]}}]
        assert match_rules("git log --oneline", rules) == "allow"
        assert match_rules("git push", rules) is None

    def test_regex_pattern(self):
        rules = [{"allow-regex": "^curl.*localhost"}]
        assert match_rules("curl http://localhost:3000", rules) == "allow"
        assert match_rules("curl http://example.com", rules) is None

    def test_deny(self):
        rules = [{"deny": "rm -rf /"}]
        assert match_rules("rm -rf /", rules) == "deny"

    def test_ask(self):
        rules = [{"ask": "git push"}]
        assert match_rules("git push origin main", rules) == "ask"

    def test_first_match_wins(self):
        rules = [
            {"deny": "rm -rf /"},
            {"allow": "rm"},
        ]
        assert match_rules("rm -rf /", rules) == "deny"

    def test_plain_assignment(self):
        assert match_rules("VAR=hello", []) == "allow"

    def test_ssh_with_ssh_rules(self):
        rules = [{"allow": "dangerous_cmd"}]
        ssh_rules = [{"allow": ["ls", "cat"]}]
        assert match_rules('ssh host "ls /foo"', rules, ssh_rules) == "allow"
        assert match_rules('ssh host "dangerous_cmd"', rules, ssh_rules) is None

    def test_ssh_without_ssh_rules(self):
        rules = [{"allow": "ls"}]
        assert match_rules('ssh host "ls /foo"', rules) is None


# ── Full evaluation ──────────────────────────────────────────────

class TestEvaluateCommand:
    @pytest.fixture()
    def rules(self):
        return [{"allow": ["echo", "cat", "head", "ls", "git log"]}]

    def test_simple_allow(self, rules):
        assert evaluate_command("echo hello", rules) == "allow"

    def test_simple_no_match(self, rules):
        assert evaluate_command("rm -rf /", rules) is None

    def test_pipeline_all_allowed(self, rules):
        assert evaluate_command("cat foo | head -5", rules) == "allow"

    def test_pipeline_one_blocked(self, rules):
        assert evaluate_command("cat foo | rm -rf /", rules) is None

    def test_pipeline_deny_wins(self):
        rules = [{"deny": "rm"}, {"allow": ["cat", "rm"]}]
        assert evaluate_command("cat foo | rm -rf /", rules) == "deny"

    def test_comment_filtered(self, rules):
        assert evaluate_command("# this is a comment\necho hello", rules) == "allow"

    def test_for_loop_body(self, rules):
        assert evaluate_command(
            'for x in 1 2; do echo $x; done',
            rules,
        ) == "allow"

    def test_for_loop_unsafe_body(self, rules):
        assert evaluate_command(
            'for x in 1 2; do rm -rf /; done',
            rules,
        ) is None

    def test_assignment_unwrap(self, rules):
        assert evaluate_command("result=$(git log --oneline -1)", rules) == "allow"

    def test_ssh_uses_ssh_rules(self):
        rules = [{"allow": "rm"}]
        ssh_rules = [{"allow": "ls"}]
        assert evaluate_command(
            'ssh host "ls /foo"',
            rules, ssh_rules,
        ) == "allow"
        assert evaluate_command(
            'ssh host "rm /foo"',
            rules, ssh_rules,
        ) is None

    def test_ssh_pipeline(self):
        ssh_rules = [{"allow": ["ls", "head", "grep"]}]
        assert evaluate_command(
            'ssh host "ls /foo | head -5"',
            [{"allow": "ssh"}], ssh_rules,
        ) == "allow"


# ── Integration: real YAML rules ────────────────────────────────

class TestRealRules:
    @pytest.fixture()
    def real_rules(self):
        from auto_approve import load_rules, load_ssh_rules
        yml = Path(__file__).parent.parent / "hooks" / "auto-approve.yml"
        return load_rules(yml), load_ssh_rules(yml)

    def test_git_local(self, real_rules):
        rules, ssh_rules = real_rules
        assert evaluate_command("git log --oneline", rules, ssh_rules) == "allow"
        assert evaluate_command("git -C /foo diff", rules, ssh_rules) == "allow"
        assert evaluate_command("git push", rules, ssh_rules) is None

    def test_pipeline(self, real_rules):
        rules, ssh_rules = real_rules
        assert evaluate_command("git log | head -5", rules, ssh_rules) == "allow"

    def test_ssh(self, real_rules):
        rules, ssh_rules = real_rules
        assert evaluate_command('ssh host "ls /foo"', rules, ssh_rules) == "allow"
        assert evaluate_command('ssh host "cat /etc/hostname"', rules, ssh_rules) == "allow"
        assert evaluate_command('ssh host "rm -rf /"', rules, ssh_rules) is None
        assert evaluate_command('ssh host "pip install foo"', rules, ssh_rules) is None

    def test_pnpm(self, real_rules):
        rules, ssh_rules = real_rules
        assert evaluate_command("pnpm build", rules, ssh_rules) == "allow"
        assert evaluate_command("pnpm deploy", rules, ssh_rules) is None

    def test_rm_safe_artifacts(self, real_rules):
        rules, ssh_rules = real_rules
        assert evaluate_command("rm -rf node_modules/.vite", rules, ssh_rules) == "allow"
        assert evaluate_command("rm -rf dist", rules, ssh_rules) == "allow"
        assert evaluate_command("rm -rf /", rules, ssh_rules) is None

    def test_gh_api_get_vs_post(self, real_rules):
        rules, ssh_rules = real_rules
        assert evaluate_command("gh api /repos/foo/pulls", rules, ssh_rules) == "allow"
        # ask-regex matches, evaluate_command returns None (not deny)
        assert evaluate_command("gh api -f body=hi /repos/foo", rules, ssh_rules) is None


# ── Spec validation ─────────────────────────────────────────────

class TestValidateSpec:
    def test_valid_with_rules_only(self, tmp_path):
        from auto_approve import validate_spec
        p = tmp_path / "spec.yml"
        p.write_text("rules:\n  - allow: ls\n")
        assert validate_spec(p) == []

    def test_valid_with_rules_and_ssh_rules(self, tmp_path):
        from auto_approve import validate_spec
        p = tmp_path / "spec.yml"
        p.write_text("rules:\n  - allow: ls\nssh-rules:\n  - allow: cat\n")
        assert validate_spec(p) == []

    def test_valid_with_anchor_keys(self, tmp_path):
        from auto_approve import validate_spec
        p = tmp_path / "spec.yml"
        p.write_text("_safe: &safe\n  - cat\n  - ls\nrules:\n  - allow: *safe\n")
        assert validate_spec(p) == []

    def test_missing_file(self, tmp_path):
        from auto_approve import validate_spec
        assert validate_spec(tmp_path / "nope.yml") == []

    def test_empty_file(self, tmp_path):
        from auto_approve import validate_spec
        p = tmp_path / "spec.yml"
        p.write_text("")
        assert validate_spec(p) == []

    def test_top_level_list(self, tmp_path):
        from auto_approve import validate_spec
        p = tmp_path / "spec.yml"
        p.write_text("- allow: ls\n- allow: cat\n")
        warnings = validate_spec(p)
        assert len(warnings) == 1
        assert "top-level is a list" in warnings[0]
        assert "no rules loaded" in warnings[0]

    def test_top_level_scalar(self, tmp_path):
        from auto_approve import validate_spec
        p = tmp_path / "spec.yml"
        p.write_text("just-a-string\n")
        warnings = validate_spec(p)
        assert len(warnings) == 1
        assert "top-level is a str" in warnings[0]

    def test_unknown_key(self, tmp_path):
        from auto_approve import validate_spec
        p = tmp_path / "spec.yml"
        p.write_text("rule:\n  - allow: ls\n")  # typo: rule (not rules)
        warnings = validate_spec(p)
        assert len(warnings) == 1
        assert "unrecognized top-level key 'rule'" in warnings[0]

    def test_multiple_unknown_keys(self, tmp_path):
        from auto_approve import validate_spec
        p = tmp_path / "spec.yml"
        p.write_text("rules:\n  - allow: ls\nfoo: 1\nbar: 2\n")
        warnings = validate_spec(p)
        assert len(warnings) == 2
        assert any("'foo'" in w for w in warnings)
        assert any("'bar'" in w for w in warnings)

    def test_yaml_parse_error(self, tmp_path):
        from auto_approve import validate_spec
        p = tmp_path / "spec.yml"
        p.write_text("rules:\n  - allow: [unclosed\n")
        warnings = validate_spec(p)
        assert len(warnings) == 1
        assert "YAML parse error" in warnings[0]
