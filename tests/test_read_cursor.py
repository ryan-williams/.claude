import json
import sys
from types import ModuleType
from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec, spec_from_loader
from pathlib import Path


def decorator(*args, **kwargs):
    def decorate(function):
        function.command = decorator
        return function
    if len(args) == 1 and callable(args[0]) and not kwargs:
        return decorate(args[0])
    return decorate


click = ModuleType('click')
click.argument = decorator
click.group = decorator
click.option = decorator
sys.modules['click'] = click

SCRIPT = Path(__file__).parents[1] / 'bin' / 'read-cursor'
LOADER = SourceFileLoader('read_cursor', str(SCRIPT))
SPEC = spec_from_loader(LOADER.name, LOADER)
read_cursor = module_from_spec(SPEC)
sys.modules[LOADER.name] = read_cursor
LOADER.exec_module(read_cursor)


def session(agent: str, uuid: str, path: Path, cwd: str, updated: float = 1) -> object:
    return read_cursor.Session(agent, uuid, path, cwd, updated)


def write_jsonl(path: Path, events: list[dict]) -> None:
    path.write_text(''.join(json.dumps(event) + '\n' for event in events))


def test_migrate_cursors_namespaces_legacy_claude_ids() -> None:
    legacy = {
        'reader': {
            'target': {
                'last_line': 12,
                'last_read_at': '2026-10-05T01:02:03Z',
                'last_timestamp': '2026-10-05T01:01:00Z',
            },
        },
        'codex:already': {
            'claude:qualified': {
                'last_line': 4,
            },
        },
    }

    assert read_cursor.migrate_cursors(legacy) == {
        'claude:reader': {
            'claude:target': {
                'last_line': 12,
                'last_read_at': '2026-10-05T01:02:03Z',
                'last_timestamp': '2026-10-05T01:01:00Z',
            },
        },
        'codex:already': {
            'claude:qualified': {
                'last_line': 4,
            },
        },
    }


def test_claude_metadata_prefers_project_bucket_over_resume_cwd(tmp_path: Path) -> None:
    project = tmp_path / '-Users-ryan-c-repo-wt-feature'
    project.mkdir()
    path = project / 'target.jsonl'
    write_jsonl(path, [{
        'type': 'user',
        'sessionId': 'target',
        'cwd': '/Users/ryan/.elsewhere',
        'message': {'content': 'Question'},
    }])

    assert read_cursor.claude_metadata(path) == ('target', '/Users/ryan/c/repo/wt/feature')


def test_default_target_prefers_other_agent_in_same_cwd(tmp_path: Path) -> None:
    reader = session('codex', 'reader', tmp_path / 'reader.jsonl', '/repo', 30)
    claude_old = session('claude', 'claude-old', tmp_path / 'claude-old.jsonl', '/repo', 10)
    claude_new = session('claude', 'claude-new', tmp_path / 'claude-new.jsonl', '/repo', 20)
    codex_newest = session('codex', 'codex-newest', tmp_path / 'codex-newest.jsonl', '/repo', 40)
    catalog = {item.key: item for item in (reader, claude_old, claude_new, codex_newest)}
    for item in catalog.values():
        write_jsonl(item.path, [{'type': 'user'}])

    assert read_cursor.resolve_target({}, reader, None, catalog) == claude_new


def test_default_target_prefers_unread_other_agent_over_last_read(tmp_path: Path) -> None:
    reader = session('codex', 'reader', tmp_path / 'reader.jsonl', '/repo', 30)
    claude = session('claude', 'claude', tmp_path / 'claude.jsonl', '/repo', 10)
    codex_peer = session('codex', 'codex-peer', tmp_path / 'codex-peer.jsonl', '/repo', 20)
    catalog = {item.key: item for item in (reader, claude, codex_peer)}
    for item in catalog.values():
        write_jsonl(item.path, [{'type': 'user'}, {'type': 'assistant'}])
    read_at = {'last_read_at': '2026-10-05T01:02:03Z'}

    # Both lines of the Claude session are already read, so the last-read peer wins.
    cursors = {reader.key: {codex_peer.key: {**read_at, 'last_line': 2}, claude.key: {'last_line': 2}}}
    assert read_cursor.resolve_target(cursors, reader, None, catalog) == codex_peer

    # Once the Claude session has an unread line, it wins over the last-read peer.
    cursors[reader.key][claude.key]['last_line'] = 1
    assert read_cursor.resolve_target(cursors, reader, None, catalog) == claude


def test_normalize_claude_messages_and_tool_call(tmp_path: Path) -> None:
    target = session('claude', 'target', tmp_path / 'target.jsonl', '/repo')
    event = {
        'type': 'assistant',
        'timestamp': '2026-10-05T01:02:03Z',
        'message': {
            'content': [
                {'type': 'text', 'text': 'Result'},
                {'type': 'tool_use', 'name': 'Bash', 'input': {'command': 'git status'}},
            ],
        },
    }

    assert read_cursor.normalize_claude(target, 7, event) == [
        {
            'source': 'claude',
            'session': 'claude:target',
            'line': 7,
            'timestamp': '2026-10-05T01:02:03Z',
            'kind': 'assistant',
            'text': 'Result',
        },
        {
            'source': 'claude',
            'session': 'claude:target',
            'line': 7,
            'timestamp': '2026-10-05T01:02:03Z',
            'kind': 'tool',
            'text': '{"command": "git status"}',
            'name': 'Bash',
        },
    ]


def test_normalize_claude_omits_synthetic_task_notification(tmp_path: Path) -> None:
    target = session('claude', 'target', tmp_path / 'target.jsonl', '/repo')
    event = {
        'type': 'user',
        'message': {
            'content': '<task-notification>\n<status>killed</status>\n</task-notification>',
        },
    }

    assert read_cursor.normalize_claude(target, 8, event) == []


def test_normalize_codex_compaction_uses_retained_context_only(tmp_path: Path) -> None:
    target = session('codex', 'target', tmp_path / 'target.jsonl', '/repo')
    event = {
        'type': 'compacted',
        'timestamp': '2026-10-05T01:02:03Z',
        'payload': {
            'retained_context': {
                'user_messages': [{'order': 1, 'text': 'Question'}],
                'assistant_messages': [{'order': 2, 'text': 'Answer'}],
            },
            'replacement_history': [{'image': 'large payload intentionally ignored'}],
        },
    }

    assert read_cursor.normalize_codex(target, 9, event) == [
        {
            'source': 'codex',
            'session': 'codex:target',
            'line': 9,
            'timestamp': '2026-10-05T01:02:03Z',
            'kind': 'user',
            'text': 'Question',
            'compacted': True,
        },
        {
            'source': 'codex',
            'session': 'codex:target',
            'line': 9,
            'timestamp': '2026-10-05T01:02:03Z',
            'kind': 'assistant',
            'text': 'Answer',
            'compacted': True,
        },
    ]


def test_first_codex_read_starts_at_latest_compaction(tmp_path: Path) -> None:
    path = tmp_path / 'target.jsonl'
    write_jsonl(path, [
        {'type': 'response_item', 'payload': {'type': 'message', 'role': 'user', 'content': [{'type': 'input_text', 'text': 'Old'}]}},
        {'type': 'compacted', 'payload': {'retained_context': {'user_messages': [{'order': 1, 'text': 'Summary'}], 'assistant_messages': []}}},
        {'type': 'response_item', 'payload': {'type': 'message', 'role': 'assistant', 'content': [{'type': 'output_text', 'text': 'New'}]}},
    ])
    target = session('codex', 'target', path, '/repo')

    after = read_cursor.first_read_after(target)

    assert after == 1
    assert read_cursor.events_after(target, after) == [
        {
            'source': 'codex',
            'session': 'codex:target',
            'line': 2,
            'timestamp': None,
            'kind': 'user',
            'text': 'Summary',
            'compacted': True,
        },
        {
            'source': 'codex',
            'session': 'codex:target',
            'line': 3,
            'timestamp': None,
            'kind': 'assistant',
            'text': 'New',
        },
    ]
