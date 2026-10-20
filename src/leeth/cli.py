"""`leeth new <name>` scaffolds a solution file; `leeth run [name]` runs one;
`leeth edit [name]` opens one in $EDITOR. Bare `leeth` runs the most recently edited problem."""

import argparse
import os
import re
import runpy
import shlex
import sys
from pathlib import Path
from typing import cast

TEMPLATE = """\
from leeth import *


class Solution:
    def solve(self, nums: list[int]) -> int:
        todo()


tests = [
    test([1, 2, 3], expected=6),
]

if __name__ == "__main__":
    run()
"""

DESIGN_TEMPLATE = """\
from leeth import *


class {cls}:
    def __init__(self):
        todo()


tests = [
    test(["{cls}"], [[]], expected=[None]),
]

if __name__ == "__main__":
    run_design()
"""


def slugify(words: list[str]) -> str:
    """'1 Two Sum' / 'https://leetcode.com/problems/two-sum/' -> '0001_two_sum'"""
    text = " ".join(words).strip()
    if m := re.search(r"leetcode\.(?:com|cn)/problems/([\w-]+)", text):
        text = m.group(1)
    text = text.lstrip("#")
    number = ""
    if m := re.match(r"(\d+)[.\s_-]*", text):
        number, text = m.group(1).zfill(4), text[m.end() :]
    slug = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
    return "_".join(p for p in (number, slug) if p) or "untitled"


def problems_dir() -> Path:
    """$LEETH_DIR, else the nearest `problems/` in or above the cwd, else ./problems."""
    if env := os.environ.get("LEETH_DIR"):
        return Path(env).expanduser()
    cwd = Path.cwd()
    for d in (cwd, *cwd.parents):
        if (d / "problems").is_dir():
            return d / "problems"
    return cwd / "problems"


def find(target: str | None) -> Path:
    problems = problems_dir()
    if target is None:
        files = sorted(problems.glob("*.py"), key=lambda p: p.stat().st_mtime)
        if not files:
            sys.exit("no problems yet - create one with `leetn new <name>`")
        return files[-1]
    if (path := Path(target)).is_file():
        return path
    needle = slugify([target])
    matches = sorted(p for p in problems.glob("*.py") if needle in p.stem)
    if len(matches) == 1:
        return matches[0]
    if not matches:
        sys.exit(f"no problem matching {target!r} in {problems}")
    sys.exit(f"{target!r} is ambiguous:\n  " + "\n  ".join(p.name for p in matches))


def cmd_new(words: list[str], design: bool) -> None:
    problems = problems_dir()
    problems.mkdir(parents=True, exist_ok=True)
    name = slugify(words)
    path = problems / f"{name}.py"
    if path.exists():
        sys.exit(f"{path} already exists")
    if design:
        cls = (
            "".join(w.capitalize() for w in re.sub(r"^\d+_?", "", name).split("_"))
            or "Design"
        )
        _ = path.write_text(DESIGN_TEMPLATE.format(cls=cls))
    else:
        _ = path.write_text(TEMPLATE)
    print(path)


def cmd_run(target: str | None) -> None:
    path = find(target)
    sys.argv = [str(path)]
    sys.path.insert(0, str(path.parent))
    _ = runpy.run_path(str(path), run_name="__main__")


def cmd_edit(target: str | None) -> None:
    path = find(target)
    editor = shlex.split(os.environ.get("EDITOR") or "vi")
    os.execvp(editor[0], [*editor, str(path)])


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="leeth",
        description="With no command, runs the most recently edited problem.",
    )
    sub = parser.add_subparsers(dest="command")

    new = sub.add_parser(
        "new", help="create a solution file in problems/ (or $LEETH_DIR)"
    )
    _ = new.add_argument(
        "name", nargs="+", help="e.g. `1 two sum`, `two-sum`, or a leetcode.com URL"
    )
    _ = new.add_argument(
        "-d",
        "--design",
        action="store_true",
        help="design problem (LRUCache, MinStack, ...)",
    )

    run = sub.add_parser(
        "run", help="run a solution file (default: most recently edited)"
    )
    _ = run.add_argument(
        "target", nargs="?", help="path, problem number, or part of the name"
    )

    edit = sub.add_parser(
        "edit",
        aliases=["e"],
        help="open a solution file in $EDITOR (default: most recently edited)",
    )
    _ = edit.add_argument(
        "target", nargs="?", help="path, problem number, or part of the name"
    )

    args = parser.parse_args()
    command = cast(str | None, args.command)
    if command == "new":
        cmd_new(cast(list[str], args.name), cast(bool, args.design))
    elif command == "run":
        cmd_run(cast(str | None, args.target))
    elif command in ("edit", "e"):
        cmd_edit(cast(str | None, args.target))
    else:
        cmd_run(None)
