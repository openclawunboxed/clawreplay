#!/usr/bin/env python3
"""
openclaw agent replay lab

standalone replay and regression runner for openclaw-style agent workflows.

this tool never calls undocumented openclaw internals.
it tests saved workflow inputs against captured outputs, shell commands, and optional jsonl session logs.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import shlex
import subprocess
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

ROOT = Path(__file__).resolve().parent
DEFAULT_RUNS_DIR = ROOT / "runs"
DEFAULT_REPORTS_DIR = ROOT / "reports"


@dataclass
class CheckResult:
    name: str
    status: str
    detail: str
    expected: Any = None
    actual: Any = None


@dataclass
class ReplayResult:
    fixture: str
    label: str
    status: str
    created_at: str
    input_path: str
    output_sha256: str
    output_chars: int
    output_excerpt: str
    checks: List[Dict[str, Any]]
    tool_sequence: List[str]
    memory_writes: List[str]
    token_total: Optional[int]
    cost_usd: Optional[float]
    command: Optional[str]
    result_path: Optional[str] = None
    markdown_report_path: Optional[str] = None


def now_stamp() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def read_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def read_text(path: Path) -> str:
    with path.open("r", encoding="utf-8", errors="replace") as f:
        return f.read()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except Exception:
        return str(path)


def resolve_path(path_value: str, base: Path) -> Path:
    p = Path(path_value).expanduser()
    if p.is_absolute():
        return p
    return (base / p).resolve()


def flatten_strings(obj: Any) -> Iterable[str]:
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from flatten_strings(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from flatten_strings(v)


def find_key_values(obj: Any, wanted: set[str]) -> Iterable[Any]:
    if isinstance(obj, dict):
        for k, v in obj.items():
            if str(k).lower() in wanted:
                yield v
            yield from find_key_values(v, wanted)
    elif isinstance(obj, list):
        for v in obj:
            yield from find_key_values(v, wanted)


def extract_tool_names(event: Dict[str, Any]) -> List[str]:
    names: List[str] = []
    candidate_keys = {"tool", "tool_name", "toolname", "name", "function", "action"}
    for value in find_key_values(event, candidate_keys):
        if isinstance(value, str):
            low = value.lower()
            if any(marker in low for marker in ["tool", "send", "write", "read", "browser", "memory", "draft", "shell", "file"]):
                names.append(value)
    # some logs use type plus nested name. keep conservative de-duplication.
    deduped: List[str] = []
    for n in names:
        if n not in deduped:
            deduped.append(n)
    return deduped


def extract_memory_write(event: Dict[str, Any]) -> List[str]:
    strings = list(flatten_strings(event))
    hits = []
    for s in strings:
        low = s.lower()
        if "memory" in low and any(word in low for word in ["write", "append", "save", "persist", "update"]):
            hits.append(s[:240])
    return hits


def extract_tokens_and_cost(event: Dict[str, Any]) -> Tuple[Optional[int], Optional[float]]:
    token_total = 0
    token_seen = False
    cost_total = 0.0
    cost_seen = False

    for key in ["tokens", "total_tokens", "token_total", "input_tokens", "output_tokens"]:
        for value in find_key_values(event, {key}):
            if isinstance(value, (int, float)):
                token_total += int(value)
                token_seen = True

    for key in ["cost", "cost_usd", "usd", "total_cost"]:
        for value in find_key_values(event, {key}):
            if isinstance(value, (int, float)):
                cost_total += float(value)
                cost_seen = True

    return (token_total if token_seen else None, cost_total if cost_seen else None)


def parse_jsonl(path: Optional[Path]) -> Tuple[List[str], List[str], Optional[int], Optional[float], List[str]]:
    if not path:
        return [], [], None, None, []
    if not path.exists():
        return [], [], None, None, [f"session jsonl not found: {path}"]

    tool_sequence: List[str] = []
    memory_writes: List[str] = []
    token_total = 0
    token_seen = False
    cost_total = 0.0
    cost_seen = False
    parse_errors: List[str] = []

    with path.open("r", encoding="utf-8", errors="replace") as f:
        for idx, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except Exception as exc:
                parse_errors.append(f"line {idx}: {exc}")
                continue
            if isinstance(event, dict):
                tool_sequence.extend(extract_tool_names(event))
                memory_writes.extend(extract_memory_write(event))
                tokens, cost = extract_tokens_and_cost(event)
                if tokens is not None:
                    token_total += tokens
                    token_seen = True
                if cost is not None:
                    cost_total += cost
                    cost_seen = True

    return tool_sequence, memory_writes, token_total if token_seen else None, cost_total if cost_seen else None, parse_errors


def command_to_argv(command: str) -> List[str]:
    try:
        return shlex.split(command, posix=(os.name != "nt"))
    except ValueError as exc:
        raise ValueError(f"could not parse command. use --shell only for trusted local commands. detail: {exc}")


def run_command(command: str, input_text: str, fixture_path: Path, timeout: int, shell: bool = False) -> str:
    env = os.environ.copy()
    env["REPLAY_INPUT_TEXT"] = input_text
    env["REPLAY_FIXTURE_PATH"] = str(fixture_path)
    env["REPLAY_INPUT_CHARS"] = str(len(input_text))

    if shell:
        command_value: Any = command
    else:
        command_value = command_to_argv(command)

    completed = subprocess.run(
        command_value,
        input=input_text,
        capture_output=True,
        text=True,
        shell=shell,
        timeout=timeout,
        env=env,
    )
    output = completed.stdout
    if completed.stderr:
        output += "\n\n[stderr]\n" + completed.stderr
    if completed.returncode != 0:
        output += f"\n\n[exit_code]\n{completed.returncode}\n"
    return output


def contains_casefold(text: str, needle: str) -> bool:
    return needle.casefold() in text.casefold()


def evaluate_output(
    fixture: Dict[str, Any],
    output_text: str,
    tool_sequence: List[str],
    memory_writes: List[str],
    token_total: Optional[int],
    cost_usd: Optional[float],
) -> List[CheckResult]:
    expected = fixture.get("expected", {})
    checks: List[CheckResult] = []

    for phrase in expected.get("must_include", []):
        ok = contains_casefold(output_text, phrase)
        checks.append(CheckResult(
            name=f"must include: {phrase}",
            status="pass" if ok else "fail",
            detail="found required phrase" if ok else "missing required phrase",
            expected=phrase,
            actual=ok,
        ))

    for phrase in expected.get("must_not_include", []):
        ok = not contains_casefold(output_text, phrase)
        checks.append(CheckResult(
            name=f"must not include: {phrase}",
            status="pass" if ok else "fail",
            detail="forbidden phrase absent" if ok else "forbidden phrase present",
            expected=f"not present: {phrase}",
            actual=not ok,
        ))

    for pattern in expected.get("regex_include", []):
        try:
            ok = re.search(pattern, output_text, re.IGNORECASE | re.MULTILINE) is not None
            detail = "regex matched" if ok else "regex did not match"
        except re.error as exc:
            ok = False
            detail = f"invalid regex: {exc}"
        checks.append(CheckResult(
            name=f"regex include: {pattern}",
            status="pass" if ok else "fail",
            detail=detail,
            expected=pattern,
            actual=ok,
        ))

    for pattern in expected.get("regex_exclude", []):
        try:
            matched = re.search(pattern, output_text, re.IGNORECASE | re.MULTILINE) is not None
            ok = not matched
            detail = "regex absent" if ok else "forbidden regex matched"
        except re.error as exc:
            ok = False
            detail = f"invalid regex: {exc}"
        checks.append(CheckResult(
            name=f"regex exclude: {pattern}",
            status="pass" if ok else "fail",
            detail=detail,
            expected=f"not match: {pattern}",
            actual=not ok,
        ))

    blocked_tools = expected.get("tools_blocked", []) or expected.get("forbidden_actions", [])
    if blocked_tools:
        lowered_tools = [t.casefold() for t in tool_sequence]
        for blocked in blocked_tools:
            found = any(blocked.casefold() in t for t in lowered_tools)
            checks.append(CheckResult(
                name=f"blocked tool/action absent: {blocked}",
                status="pass" if not found else "fail",
                detail="not observed" if not found else "observed in tool sequence",
                expected=f"not observed: {blocked}",
                actual=found,
            ))

    allowed_tools = expected.get("tools_allowed", []) or expected.get("allowed_actions", [])
    if allowed_tools and tool_sequence:
        lowered_allowed = [a.casefold() for a in allowed_tools]
        unexpected = []
        for tool in tool_sequence:
            low = tool.casefold()
            if not any(a in low or low in a for a in lowered_allowed):
                unexpected.append(tool)
        checks.append(CheckResult(
            name="only allowed tools/actions observed",
            status="pass" if not unexpected else "review",
            detail="no unexpected tools" if not unexpected else f"unexpected tools need review: {unexpected}",
            expected=allowed_tools,
            actual=unexpected,
        ))

    max_tool_calls = expected.get("max_tool_calls")
    if isinstance(max_tool_calls, int):
        ok = len(tool_sequence) <= max_tool_calls
        checks.append(CheckResult(
            name="max tool calls",
            status="pass" if ok else "review",
            detail=f"observed {len(tool_sequence)} tool calls",
            expected=max_tool_calls,
            actual=len(tool_sequence),
        ))

    allow_memory_writes = expected.get("allow_memory_writes", False)
    if not allow_memory_writes:
        ok = len(memory_writes) == 0
        checks.append(CheckResult(
            name="no memory writes",
            status="pass" if ok else "fail",
            detail="no memory writes observed" if ok else "memory write-like events observed",
            expected="none",
            actual=memory_writes,
        ))

    max_tokens = expected.get("max_tokens")
    if isinstance(max_tokens, int) and token_total is not None:
        ok = token_total <= max_tokens
        checks.append(CheckResult(
            name="max tokens",
            status="pass" if ok else "review",
            detail=f"observed {token_total} tokens",
            expected=max_tokens,
            actual=token_total,
        ))

    max_cost = expected.get("max_cost_usd")
    if isinstance(max_cost, (int, float)) and cost_usd is not None:
        ok = cost_usd <= float(max_cost)
        checks.append(CheckResult(
            name="max cost usd",
            status="pass" if ok else "review",
            detail=f"observed ${cost_usd:.6f}",
            expected=float(max_cost),
            actual=cost_usd,
        ))

    if expected.get("review_required", False):
        checks.append(CheckResult(
            name="human review required",
            status="review",
            detail="fixture marks this workflow as needing human review before real-world action",
            expected=True,
            actual=True,
        ))

    return checks


def overall_status(checks: List[CheckResult]) -> str:
    if any(c.status == "fail" for c in checks):
        return "fail"
    if any(c.status == "review" for c in checks):
        return "needs_review"
    return "pass"


def make_markdown_result(result: ReplayResult, fixture: Dict[str, Any]) -> str:
    lines = []
    lines.append(f"# replay result: {result.fixture}")
    lines.append("")
    lines.append(f"label: {result.label}")
    lines.append(f"status: {result.status}")
    lines.append(f"created_at: {result.created_at}")
    lines.append(f"input: {result.input_path}")
    lines.append(f"output_sha256: {result.output_sha256}")
    lines.append(f"output_chars: {result.output_chars}")
    if result.token_total is not None:
        lines.append(f"tokens: {result.token_total}")
    if result.cost_usd is not None:
        lines.append(f"cost_usd: {result.cost_usd:.6f}")
    lines.append("")
    lines.append("## checks")
    lines.append("")
    for check in result.checks:
        lines.append(f"- {check['status']}: {check['name']} - {check['detail']}")
    lines.append("")
    lines.append("## output excerpt")
    lines.append("")
    lines.append("```text")
    lines.append(result.output_excerpt)
    lines.append("```")
    if result.tool_sequence:
        lines.append("")
        lines.append("## observed tool sequence")
        for t in result.tool_sequence:
            lines.append(f"- {t}")
    if result.memory_writes:
        lines.append("")
        lines.append("## memory write-like events")
        for m in result.memory_writes:
            lines.append(f"- {m}")
    lines.append("")
    lines.append("## operator note")
    lines.append("")
    lines.append("pass means the output matched the written expectations. needs_review means a human should inspect before trusting the workflow. fail means the output violated a rule.")
    lines.append("")
    return "\n".join(lines)


def command_run(args: argparse.Namespace) -> int:
    fixture_path = Path(args.fixture).expanduser().resolve()
    fixture = read_json(fixture_path)
    fixture_base = fixture_path.parent

    input_path = resolve_path(fixture["input"]["path"], fixture_base)
    input_text = read_text(input_path)

    command = args.command or fixture.get("runner", {}).get("command")
    actual_file = args.actual or fixture.get("actual_output_path")

    if command:
        output_text = run_command(command, input_text, fixture_path, args.timeout, shell=args.shell)
    elif actual_file:
        actual_base = Path.cwd() if args.actual else fixture_base
        actual_path = resolve_path(actual_file, actual_base)
        output_text = read_text(actual_path)
    else:
        sample = fixture.get("sample_output", {})
        if isinstance(sample, dict) and sample.get("path"):
            output_text = read_text(resolve_path(sample["path"], fixture_base))
        else:
            print("no --command, --actual, actual_output_path, or sample_output.path found", file=sys.stderr)
            return 2

    session_path = Path(args.session_jsonl).expanduser().resolve() if args.session_jsonl else None
    tool_sequence, memory_writes, token_total, cost_usd, parse_errors = parse_jsonl(session_path)

    checks = evaluate_output(fixture, output_text, tool_sequence, memory_writes, token_total, cost_usd)
    for err in parse_errors:
        checks.append(CheckResult(name="session jsonl parse", status="review", detail=err))

    label = args.label or "run"
    created = now_stamp()
    result_name = f"{fixture.get('name', fixture_path.stem)}_{label}_{created}"
    result_json_path = Path(args.out).expanduser().resolve() / f"{result_name}.json"
    result_md_path = DEFAULT_REPORTS_DIR / f"{result_name}.md" if args.report_out is None else Path(args.report_out).expanduser().resolve() / f"{result_name}.md"

    result = ReplayResult(
        fixture=fixture.get("name", fixture_path.stem),
        label=label,
        status=overall_status(checks),
        created_at=created,
        input_path=rel(input_path),
        output_sha256=sha256_text(output_text),
        output_chars=len(output_text),
        output_excerpt=output_text[:2000],
        checks=[asdict(c) for c in checks],
        tool_sequence=tool_sequence,
        memory_writes=memory_writes,
        token_total=token_total,
        cost_usd=cost_usd,
        command=command,
        result_path=rel(result_json_path),
        markdown_report_path=rel(result_md_path),
    )

    write_json(result_json_path, asdict(result))
    result_md_path.parent.mkdir(parents=True, exist_ok=True)
    result_md_path.write_text(make_markdown_result(result, fixture), encoding="utf-8")

    print(f"status: {result.status}")
    print(f"json: {rel(result_json_path)}")
    print(f"report: {rel(result_md_path)}")
    return 1 if result.status == "fail" and args.fail_exit else 0


def load_result(path: Path) -> Dict[str, Any]:
    return read_json(path)


def compare_lists(a: List[Any], b: List[Any]) -> Dict[str, Any]:
    return {
        "same": a == b,
        "before_only": [x for x in a if x not in b],
        "after_only": [x for x in b if x not in a],
        "before": a,
        "after": b,
    }


def command_compare(args: argparse.Namespace) -> int:
    before_path = Path(args.before).expanduser().resolve()
    after_path = Path(args.after).expanduser().resolve()
    before = load_result(before_path)
    after = load_result(after_path)

    checks_before = {c["name"]: c for c in before.get("checks", [])}
    checks_after = {c["name"]: c for c in after.get("checks", [])}
    all_check_names = sorted(set(checks_before) | set(checks_after))
    changed_checks = []
    for name in all_check_names:
        b = checks_before.get(name, {}).get("status")
        a = checks_after.get(name, {}).get("status")
        if b != a:
            changed_checks.append({"name": name, "before": b, "after": a})

    token_delta = None
    if before.get("token_total") is not None and after.get("token_total") is not None:
        token_delta = after["token_total"] - before["token_total"]

    cost_delta = None
    if before.get("cost_usd") is not None and after.get("cost_usd") is not None:
        cost_delta = after["cost_usd"] - before["cost_usd"]

    comparison = {
        "created_at": now_stamp(),
        "before": rel(before_path),
        "after": rel(after_path),
        "fixture_before": before.get("fixture"),
        "fixture_after": after.get("fixture"),
        "status_before": before.get("status"),
        "status_after": after.get("status"),
        "output_hash_same": before.get("output_sha256") == after.get("output_sha256"),
        "output_chars_before": before.get("output_chars"),
        "output_chars_after": after.get("output_chars"),
        "tool_sequence": compare_lists(before.get("tool_sequence", []), after.get("tool_sequence", [])),
        "memory_writes": compare_lists(before.get("memory_writes", []), after.get("memory_writes", [])),
        "token_total_before": before.get("token_total"),
        "token_total_after": after.get("token_total"),
        "token_delta": token_delta,
        "cost_usd_before": before.get("cost_usd"),
        "cost_usd_after": after.get("cost_usd"),
        "cost_delta": cost_delta,
        "changed_checks": changed_checks,
    }

    out_dir = Path(args.out).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    name = f"compare_{before.get('fixture','before')}_{after.get('label','after')}_{now_stamp()}"
    json_path = out_dir / f"{name}.json"
    md_path = out_dir / f"{name}.md"
    write_json(json_path, comparison)
    md_path.write_text(make_compare_markdown(comparison), encoding="utf-8")

    print(f"comparison json: {rel(json_path)}")
    print(f"comparison report: {rel(md_path)}")
    changed = before.get("status") != after.get("status") or bool(changed_checks)
    if changed:
        print("comparison status: changed")
    else:
        print("comparison status: no status change")
    if changed and getattr(args, "fail_on_change", False):
        return 1
    return 0


def make_compare_markdown(comparison: Dict[str, Any]) -> str:
    lines = ["# replay comparison", ""]
    lines.append(f"before: {comparison['before']}")
    lines.append(f"after: {comparison['after']}")
    lines.append(f"status_before: {comparison['status_before']}")
    lines.append(f"status_after: {comparison['status_after']}")
    lines.append(f"output_hash_same: {comparison['output_hash_same']}")
    lines.append("")
    lines.append("## size")
    lines.append(f"before chars: {comparison['output_chars_before']}")
    lines.append(f"after chars: {comparison['output_chars_after']}")
    lines.append("")
    lines.append("## cost shape")
    lines.append(f"tokens before: {comparison['token_total_before']}")
    lines.append(f"tokens after: {comparison['token_total_after']}")
    lines.append(f"token delta: {comparison['token_delta']}")
    lines.append(f"cost before: {comparison['cost_usd_before']}")
    lines.append(f"cost after: {comparison['cost_usd_after']}")
    lines.append(f"cost delta: {comparison['cost_delta']}")
    lines.append("")
    lines.append("## changed checks")
    if comparison["changed_checks"]:
        for c in comparison["changed_checks"]:
            lines.append(f"- {c['name']}: {c['before']} -> {c['after']}")
    else:
        lines.append("- none")
    lines.append("")
    lines.append("## tool sequence")
    ts = comparison["tool_sequence"]
    lines.append(f"same: {ts['same']}")
    if ts["before_only"]:
        lines.append(f"before only: {ts['before_only']}")
    if ts["after_only"]:
        lines.append(f"after only: {ts['after_only']}")
    lines.append("")
    lines.append("## memory writes")
    mw = comparison["memory_writes"]
    lines.append(f"same: {mw['same']}")
    if mw["before_only"]:
        lines.append(f"before only: {mw['before_only']}")
    if mw["after_only"]:
        lines.append(f"after only: {mw['after_only']}")
    lines.append("")
    lines.append("## operator read")
    lines.append("if the later run changed status, allowed actions, memory writes, or cost shape, hold that workflow back and inspect the layer you changed.")
    lines.append("")
    return "\n".join(lines)


def fixture_errors(path: Path) -> List[str]:
    errors: List[str] = []
    try:
        fixture = read_json(path)
    except Exception as exc:
        return [f"invalid json: {exc}"]

    for key in ["name", "input", "expected"]:
        if key not in fixture:
            errors.append(f"missing required key: {key}")

    if not isinstance(fixture.get("name", ""), str) or not fixture.get("name", "").strip():
        errors.append("name must be a non-empty string")

    input_block = fixture.get("input", {})
    if not isinstance(input_block, dict):
        errors.append("input must be an object")
    elif "path" not in input_block:
        errors.append("missing input.path")
    else:
        input_path = resolve_path(str(input_block["path"]), path.parent)
        if not input_path.exists():
            errors.append(f"input path not found: {input_block['path']}")

    expected = fixture.get("expected", {})
    if not isinstance(expected, dict):
        errors.append("expected must be an object")
    else:
        list_keys = ["must_include", "must_not_include", "regex_include", "regex_exclude", "tools_allowed", "tools_blocked"]
        for key in list_keys:
            if key in expected and not isinstance(expected[key], list):
                errors.append(f"expected.{key} must be a list")
        int_keys = ["max_tool_calls", "max_tokens"]
        for key in int_keys:
            if key in expected and not isinstance(expected[key], int):
                errors.append(f"expected.{key} must be an integer")
        if "max_cost_usd" in expected and not isinstance(expected["max_cost_usd"], (int, float)):
            errors.append("expected.max_cost_usd must be a number")
        if "allow_memory_writes" in expected and not isinstance(expected["allow_memory_writes"], bool):
            errors.append("expected.allow_memory_writes must be true or false")
        if "review_required" in expected and not isinstance(expected["review_required"], bool):
            errors.append("expected.review_required must be true or false")

    sample = fixture.get("sample_output")
    if isinstance(sample, dict) and sample.get("path"):
        sample_path = resolve_path(str(sample["path"]), path.parent)
        if not sample_path.exists():
            errors.append(f"sample output not found: {sample['path']}")

    return errors


def command_validate(args: argparse.Namespace) -> int:
    path = Path(args.fixture).expanduser().resolve()
    errors = fixture_errors(path)
    if errors:
        for e in errors:
            print(f"fail: {path.name}: {e}")
        return 1
    print(f"pass: {path.name} looks usable")
    return 0


def command_validate_all(args: argparse.Namespace) -> int:
    root = Path(args.path).expanduser().resolve()
    files = sorted(root.glob("*.json"))
    if not files:
        print(f"fail: no fixture json files found in {root}")
        return 1
    failed = 0
    for f in files:
        errors = fixture_errors(f)
        if errors:
            failed += 1
            for e in errors:
                print(f"fail: {f.name}: {e}")
        else:
            print(f"pass: {f.name}")
    if failed:
        print(f"summary: {failed} fixture files failed validation")
        return 1
    print(f"summary: {len(files)} fixture files passed")
    return 0


def command_doctor(args: argparse.Namespace) -> int:
    problems: List[str] = []
    if sys.version_info < (3, 10):
        problems.append("python 3.10 or newer is recommended")
    for folder in ["fixtures", "inputs", "outputs", "runs", "reports", "docs", "templates", "examples"]:
        if not (ROOT / folder).exists():
            problems.append(f"missing folder: {folder}")
    fixture_problems = []
    for f in sorted((ROOT / "fixtures").glob("*.json")):
        for e in fixture_errors(f):
            fixture_problems.append(f"{f.name}: {e}")
    problems.extend(fixture_problems)
    print(f"python: {sys.version.split()[0]}")
    print(f"repo: {ROOT}")
    if problems:
        for p in problems:
            print(f"fail: {p}")
        return 1
    print("pass: repo doctor checks completed")
    return 0


def command_scan_sessions(args: argparse.Namespace) -> int:
    root = Path(args.path).expanduser().resolve()
    if not root.exists():
        print(f"not found: {root}", file=sys.stderr)
        return 2
    files = sorted(root.rglob("*.jsonl"))
    rows = []
    for f in files:
        tool_sequence, memory_writes, tokens, cost, errors = parse_jsonl(f)
        rows.append({
            "file": rel(f),
            "tools": tool_sequence,
            "memory_writes": memory_writes,
            "tokens": tokens,
            "cost_usd": cost,
            "parse_errors": errors[:5],
        })
    out = Path(args.out).expanduser().resolve()
    write_json(out, {"scanned_at": now_stamp(), "root": str(root), "files": rows})
    print(f"scanned {len(files)} jsonl files")
    print(f"report: {rel(out)}")
    return 0


def command_init(args: argparse.Namespace) -> int:
    target = Path(args.path).expanduser().resolve()
    if target.exists() and any(target.iterdir()) and not args.force:
        print("target exists and is not empty. pass --force to write anyway", file=sys.stderr)
        return 2
    target.mkdir(parents=True, exist_ok=True)
    template = ROOT / "templates" / "fixture.template.json"
    if template.exists():
        dest = target / "fixture.template.json"
        dest.write_text(template.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"created starter fixture folder: {target}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="openclaw agent replay lab")
    sub = p.add_subparsers(dest="command_name", required=True)

    r = sub.add_parser("run", help="run one replay fixture")
    r.add_argument("fixture", help="path to fixture json")
    r.add_argument("--actual", help="captured output file to score")
    r.add_argument("--command", help="shell command to run. input text is passed on stdin and REPLAY_INPUT_TEXT")
    r.add_argument("--session-jsonl", help="optional openclaw-style session jsonl file to inspect")
    r.add_argument("--label", default="run", help="label such as before, after, model-test, skill-test")
    r.add_argument("--out", default=str(DEFAULT_RUNS_DIR), help="directory for json results")
    r.add_argument("--report-out", default=None, help="directory for markdown reports")
    r.add_argument("--timeout", type=int, default=120, help="command timeout seconds")
    r.add_argument("--fail-exit", action="store_true", help="exit 1 when fixture fails")
    r.add_argument("--shell", action="store_true", help="run command through the shell. use only for trusted local adapters")
    r.set_defaults(func=command_run)

    c = sub.add_parser("compare", help="compare two replay result json files")
    c.add_argument("before")
    c.add_argument("after")
    c.add_argument("--out", default=str(DEFAULT_REPORTS_DIR))
    c.add_argument("--fail-on-change", action="store_true", help="exit 1 when the comparison changed")
    c.set_defaults(func=command_compare)

    v = sub.add_parser("validate", help="validate a fixture shape")
    v.add_argument("fixture")
    v.set_defaults(func=command_validate)

    va = sub.add_parser("validate-all", help="validate every fixture json file in a folder")
    va.add_argument("path", nargs="?", default="fixtures")
    va.set_defaults(func=command_validate_all)

    d = sub.add_parser("doctor", help="check python version, folders, and bundled fixtures")
    d.set_defaults(func=command_doctor)

    s = sub.add_parser("scan-sessions", help="scan a folder of jsonl session logs without assuming a fixed schema")
    s.add_argument("path", help="folder containing jsonl files")
    s.add_argument("--out", default=str(DEFAULT_REPORTS_DIR / "session_scan.json"))
    s.set_defaults(func=command_scan_sessions)

    i = sub.add_parser("init", help="create a starter fixture folder")
    i.add_argument("path")
    i.add_argument("--force", action="store_true")
    i.set_defaults(func=command_init)
    return p


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
