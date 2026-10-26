"""HW7 Part 6 file tools and a pure-Python command safety gate.

The demonstration at the bottom creates and changes files only in a temporary
course sandbox directory.  The ``bash`` tool is intentionally a safety gate:
it reports whether a command may run, but does not execute shell commands.
"""

from __future__ import annotations

import difflib
import json
import tempfile
from pathlib import Path
from typing import Any

# Commands that are normally read-only or informational.  ``is_destructive``
# is checked separately, so a destructive Git subcommand is still blocked.
SAFE_PREFIXES = ("git ", "ls", "pwd", "rg ", "python --version")


def _sandbox_path(sandbox: Path, path: str) -> Path:
    """Resolve ``path`` and reject paths outside the supplied sandbox."""
    root = sandbox.resolve()
    candidate = (root / path).resolve()
    if candidate != root and root not in candidate.parents:
        raise ValueError("Path must stay inside the course sandbox.")
    return candidate


def read_file(sandbox: Path, path: str, max_lines: int | None = None) -> dict[str, Any]:
    """Read a sandboxed text file, optionally returning only its first lines."""
    target = _sandbox_path(sandbox, path)
    lines = target.read_text(encoding="utf-8").splitlines(keepends=True)
    shown = lines if max_lines is None else lines[:max_lines]
    return {"path": str(target), "content": "".join(shown), "line_count": len(shown)}


def write_file(sandbox: Path, path: str, content: str) -> dict[str, Any]:
    """Create or replace one text file inside the sandbox."""
    target = _sandbox_path(sandbox, path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return {"path": str(target), "bytes_written": len(content.encode("utf-8"))}


def edit_file(sandbox: Path, path: str, old: str, new: str) -> dict[str, Any]:
    """Replace one exact string and return a short unified diff."""
    target = _sandbox_path(sandbox, path)
    before = target.read_text(encoding="utf-8")
    if old not in before:
        raise ValueError("The requested text was not found.")
    after = before.replace(old, new, 1)
    target.write_text(after, encoding="utf-8")
    diff = "".join(
        difflib.unified_diff(
            before.splitlines(keepends=True),
            after.splitlines(keepends=True),
            fromfile=path,
            tofile=path,
            n=1,
        )
    )
    return {"path": str(target), "diff": diff[:500]}


def glob_files(sandbox: Path, pattern: str) -> dict[str, Any]:
    """List files in the sandbox matching a glob pattern."""
    root = sandbox.resolve()
    matches = [
        str(item.relative_to(root)) for item in root.glob(pattern) if item.is_file()
    ]
    return {"pattern": pattern, "matches": sorted(matches)}


def search_in_files(
    sandbox: Path, query: str, file_pattern: str = "**/*"
) -> dict[str, Any]:
    """Find text matches in sandbox files selected by ``file_pattern``."""
    root = sandbox.resolve()
    matches: list[dict[str, Any]] = []
    for item in root.glob(file_pattern):
        if not item.is_file():
            continue
        lines = item.read_text(encoding="utf-8").splitlines()
        for line_number, line in enumerate(lines, 1):
            if query in line:
                matches.append(
                    {
                        "path": str(item.relative_to(root)),
                        "line": line_number,
                        "text": line,
                    }
                )
    return {"query": query, "file_pattern": file_pattern, "matches": matches}


def is_destructive(command: str) -> bool:
    """Return whether a command contains a known destructive operation."""
    normalized = command.strip().lower()
    destructive_markers = (
        "rm -r",
        "rm -f",
        "rmdir ",
        "unlink ",
        "git reset --hard",
        "git clean",
        "sudo ",
        "doas ",
        "chmod ",
        "chown ",
        "dd ",
        "mkfs",
        "> /",
        ">>/",
    )
    return any(marker in normalized for marker in destructive_markers)


def confirm_bash(command: str, auto_approve: bool = False) -> dict[str, Any]:
    """Apply the allow-list and destructive-command confirmation contract."""
    destructive = is_destructive(command)
    if destructive and not auto_approve:
        return {
            "allowed": False,
            "reason": "Destructive command needs explicit confirmation.",
        }
    if not command.strip().startswith(SAFE_PREFIXES):
        return {"allowed": False, "reason": "Command is not on SAFE_PREFIXES."}
    if destructive:
        return {"allowed": True, "reason": "Destructive command explicitly confirmed."}
    return {"allowed": True, "reason": "Command matches SAFE_PREFIXES."}


def bash(command: str, auto_approve: bool = False) -> dict[str, Any]:
    """Return the safety-gate decision without running a shell command."""
    return confirm_bash(command, auto_approve=auto_approve)


def run_demo() -> dict[str, Any]:
    """Run the required file-tool integration and 5-pass/5-block gate tests."""
    with tempfile.TemporaryDirectory(prefix="data260_hw7_part6_") as directory:
        sandbox = Path(directory)
        write_file(sandbox, "alpha.py", "INFO = True\n")
        write_file(sandbox, "beta.py", "DEBUG = True\nprint('debug enabled')\n")
        write_file(sandbox, "gamma.py", "WARNING = True\n")

        listed = glob_files(sandbox, "*.py")
        found = search_in_files(sandbox, "DEBUG", file_pattern="*.py")
        debug_file = found["matches"][0]["path"]
        contents = read_file(sandbox, debug_file, max_lines=10)
        edited = edit_file(sandbox, "alpha.py", "INFO", "INFO_LEVEL")

        allowed_commands = ["pwd", "ls", "rg DEBUG", "python --version", "git status"]
        blocked_commands = [
            "git reset --hard",
            "rm -rf temporary_data",
            "sudo whoami",
            "chmod 777 alpha.py",
            "dd if=/dev/zero of=/dev/disk1",
        ]
        command_results = [
            {"command": command, "expected": "allow", **bash(command)}
            for command in allowed_commands
        ] + [
            {"command": command, "expected": "block", **bash(command)}
            for command in blocked_commands
        ]
        passed = all(
            (result["expected"] == "allow") == result["allowed"]
            for result in command_results
        )
        return {
            "integration": {
                "glob_matches": listed["matches"],
                "search_matches": found["matches"],
                "read_result": contents,
                "edit_diff": edited["diff"],
            },
            "safety_gate": {
                "results": command_results,
                "all_expectations_passed": passed,
            },
        }


if __name__ == "__main__":
    results = run_demo()
    raw_results = (
        Path(__file__).resolve().parent.parent
        / "reports"
        / "hw07"
        / "raw"
        / "part6_safety_gate_results.json"
    )
    raw_results.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(results, indent=2))
