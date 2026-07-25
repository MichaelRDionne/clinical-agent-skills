#!/usr/bin/env python3
"""Validate YAML frontmatter on every skill and command file.

This repo's product IS the frontmatter: Claude Code loads a skill by matching
its `description` field, and a command's `description` is what a human or
another agent sees before invoking it. A skill with broken or missing
frontmatter fails silently — it just never gets loaded — so there is no
natural signal when an edit breaks it. This script is that signal.

Checks per file:
  - starts with a `---` line and has a matching closing `---`
  - the frontmatter block parses as valid YAML
  - required keys are present and non-empty:
      skills/*/SKILL.md  -> name, description
      commands/*.md       -> description
  - for SKILL.md, `name` matches the parent directory name (the loader keys
    off the directory, not the declared name, so drift here is a real bug)

Usage:
    python3 scripts/lint_frontmatter.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent


def extract_frontmatter(path: Path) -> dict | None:
    """Return the parsed frontmatter dict, or None if the file has no
    well-formed `---`-delimited block at the top."""
    lines = path.read_text().splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    try:
        end = lines.index("---", 1)
    except ValueError:
        return None
    block = "\n".join(lines[1:end])
    return yaml.safe_load(block) or {}


def check_file(path: Path, required_keys: list[str]) -> list[str]:
    errors = []
    frontmatter = extract_frontmatter(path)
    rel = path.relative_to(REPO_ROOT)

    if frontmatter is None:
        return [f"{rel}: missing or malformed '---' frontmatter block"]

    if not isinstance(frontmatter, dict):
        return [f"{rel}: frontmatter did not parse to a mapping"]

    for key in required_keys:
        value = frontmatter.get(key)
        if value is None or (isinstance(value, str) and not value.strip()):
            errors.append(f"{rel}: missing or empty required key '{key}'")

    if "name" in required_keys:
        declared = frontmatter.get("name")
        expected = path.parent.name
        if declared and declared != expected:
            errors.append(
                f"{rel}: frontmatter name '{declared}' does not match "
                f"parent directory '{expected}' (Claude Code loads by directory)"
            )

    return errors


def main() -> int:
    errors: list[str] = []

    skill_files = sorted(REPO_ROOT.glob("skills/*/SKILL.md"))
    command_files = sorted(REPO_ROOT.glob("commands/*.md"))

    if not skill_files:
        errors.append("no skills/*/SKILL.md files found — did the glob path change?")
    if not command_files:
        errors.append("no commands/*.md files found — did the glob path change?")

    for f in skill_files:
        errors.extend(check_file(f, required_keys=["name", "description"]))

    for f in command_files:
        errors.extend(check_file(f, required_keys=["description"]))

    if errors:
        print(f"FAIL — {len(errors)} frontmatter issue(s):\n")
        for e in errors:
            print(f"  - {e}")
        return 1

    print(f"OK — {len(skill_files)} skill(s), {len(command_files)} command(s) all have valid frontmatter.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
