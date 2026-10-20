"""Run a Solution against test cases and print a readable report."""

import annotationlib
import copy
import inspect
import math
import sys
import time
import traceback
import types
import typing
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from typing import Any, Union, cast  # pyright: ignore[reportDeprecated]

from .structures import (
    ListNode,
    TreeNode,
    linked_to_list,
    list_to_linked,
    list_to_tree,
    tree_to_list,
)

_MISSING = object()


@dataclass
class Case:
    args: tuple[object, ...]
    kwargs: dict[str, object] = field(default_factory=dict)
    expected: object = _MISSING
    any_order: bool = False
    check: Callable[..., bool] | None = None


def test(
    *args: object,
    expected: object = _MISSING,
    any_order: bool = False,
    check: Callable[..., bool] | None = None,
    **kwargs: object,
) -> Case:
    """One test case. Positional/keyword args are passed straight to the method.

    expected   -- the answer, in LeetCode's plain form (lists for linked lists/trees).
                  Omit it to just print what the solution returns.
    any_order  -- treat lists (at every depth) as unordered when comparing.
    check      -- custom validator for problems with several valid answers or that
                  mutate their input. Either `check(got)` or
                  `check(got, *args, **kwargs)`, where args are the method's arguments
                  *after* the call (so in-place changes are visible).
    """
    return Case(
        args=args, kwargs=kwargs, expected=expected, any_order=any_order, check=check
    )


# Keep pytest from collecting the helper when it's imported into a test module.
test.__test__ = False  # pyright: ignore[reportFunctionMemberAccess]  # ty: ignore[unresolved-attribute]


# --- output -----------------------------------------------------------------

_COLOR = sys.stdout.isatty()

# repr() truncation limits: values in result lines, arguments in a case's label,
# and an operation's arguments in a design-problem mismatch.
_REPR_LIMIT = 300
_ARG_LIMIT = 120
_OP_ARG_LIMIT = 80

_STATUS_COLOR = {"PASS": "1;32", "FAIL": "1;31", "ERR ": "1;31", "OUT ": "1;33"}


def _c(code: str, text: str) -> str:
    return f"\033[{code}m{text}\033[0m" if _COLOR else text


def _short(value: object, limit: int = _REPR_LIMIT) -> str:
    s = repr(value)
    return s if len(s) <= limit else s[: limit - 3] + "..."


def _cases(n: int) -> str:
    return f"{n} case" + ("" if n == 1 else "s")


def _format_error(e: Exception) -> str:
    # Skip the first frame: it's the runner's own call into the solution.
    tb = e.__traceback__.tb_next if e.__traceback__ else None
    text = "".join(traceback.format_exception(type(e), e, tb)).strip()
    return _c("31", "     " + text.replace("\n", "\n     "))


@dataclass
class _Outcome:
    label: str  # what's shown after "#i"
    ok: bool | None  # None: no expectation, just print the result (OUT)
    elapsed: float = 0.0
    error: Exception | None = None
    details: list[str] = field(default_factory=list)  # lines under the status line


def _status(outcome: _Outcome) -> str:
    if outcome.error is not None:
        return "ERR "
    if outcome.ok is None:
        return "OUT "
    return "PASS" if outcome.ok else "FAIL"


def _run_cases(title: str, count: int, outcomes: Iterable[_Outcome]) -> bool:
    """Print a header, one block per outcome and a summary. True if nothing failed."""
    print(_c("1", title) + _c("2", f"  ({_cases(count)})"))
    results: list[bool] = []
    total_time = 0.0
    for i, outcome in enumerate(outcomes, 1):
        status = _status(outcome)
        line = f"{_c(_STATUS_COLOR[status], status)} #{i}  {outcome.label}"
        if outcome.error is not None:
            print(line)
            print(_format_error(outcome.error))
        else:
            print(line + _c("2", f"  {outcome.elapsed * 1000:.2f} ms"))
            for detail in outcome.details:
                print(f"     {detail}")
        total_time += outcome.elapsed
        if outcome.ok is not None:
            results.append(outcome.ok)

    passed, total = sum(results), len(results)
    color = "32" if passed == total else "31"
    print(
        _c(f"1;{color}", f"\n{passed}/{total} passed")
        + _c("2", f"  ({total_time * 1000:.2f} ms total)")
    )
    return passed == total


# --- conversion between LeetCode plain values and node structures ---------


def _to_input(value: object, hint: object) -> object:
    origin = typing.get_origin(hint)
    hint_args = cast(tuple[object, ...], typing.get_args(hint))
    # typing.Union covers Optional[X] / Union[X, None]; UnionType covers X | None.
    if origin in (Union, types.UnionType):  # pyright: ignore[reportDeprecated]
        if value is None:
            return None
        hint = next((h for h in hint_args if h is not type(None)), None)
        return _to_input(value, hint)
    if not isinstance(value, list):
        return value
    items = cast(list[object], value)
    if hint is ListNode:
        return list_to_linked(cast(list[int], items))
    if hint is TreeNode:
        return list_to_tree(cast(list[int | None], items))
    if origin is list and hint_args:
        return [_to_input(v, hint_args[0]) for v in items]
    return items


def _is_node_hint(hint: object) -> bool:
    """Whether `hint` is ListNode/TreeNode, or a union/generic that mentions one."""
    return bool({ListNode, TreeNode} & {hint, *typing.get_args(hint)})


def _to_plain(value: object, hint: object = None) -> object:
    # A None ListNode/TreeNode result is an empty list in LeetCode's notation.
    if value is None and hint is not None and _is_node_hint(hint):
        return list[object]()
    if isinstance(value, ListNode):
        return linked_to_list(value)
    if isinstance(value, TreeNode):
        return tree_to_list(value)
    if isinstance(value, (list, tuple)):
        return [_to_plain(v) for v in cast(list[object], value)]
    return value


# --- comparison ---------------------------------------------------------------


def _sort_key(value: object) -> tuple[int, object]:
    # Numbers sort by value rather than repr, so floats that _equal treats as
    # equal land in the same position on both sides.
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return (0, float(value))
    if isinstance(value, list):
        return (1, tuple(_sort_key(v) for v in cast(list[object], value)))
    return (2, repr(value))


def _unordered(value: object) -> object:
    if isinstance(value, list):
        items = [_unordered(v) for v in cast(list[object], value)]
        return sorted(items, key=_sort_key)
    return value


def _equal(a: object, b: object) -> bool:
    if isinstance(a, float) or isinstance(b, float):
        if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
            return False
        return math.isclose(a, b, rel_tol=1e-5, abs_tol=1e-5)
    if isinstance(a, list) and isinstance(b, list):
        xs, ys = cast(list[object], a), cast(list[object], b)
        return len(xs) == len(ys) and all(_equal(x, y) for x, y in zip(xs, ys))
    return a == b


# --- run ----------------------------------------------------------------------


def _wants_args(check: Callable[..., bool]) -> bool:
    """Whether `check` takes the method's arguments as well as its return value."""
    try:
        params = inspect.signature(check).parameters.values()
    except TypeError, ValueError:
        return True
    positional = (
        inspect.Parameter.POSITIONAL_ONLY,
        inspect.Parameter.POSITIONAL_OR_KEYWORD,
    )
    # Parameters with defaults are options of the check, not slots for arguments.
    required = [p for p in params if p.kind in positional and p.default is p.empty]  # pyright: ignore[reportAny]
    return any(p.kind is inspect.Parameter.VAR_POSITIONAL for p in params) or (
        len(required) > 1
    )


def _pick_method(cls: type, name: str | None) -> str:
    if name:
        return name
    methods = [n for n, v in vars(cls).items() if callable(v) and not n.startswith("_")]  # pyright: ignore[reportAny]
    if not methods:
        raise ValueError(f"{cls.__name__} has no public methods")
    return methods[0]


def _type_hints(func: Callable[..., object]) -> dict[str, object]:
    try:
        return typing.get_type_hints(func)
    except Exception as e:  # noqa: BLE001
        print(
            _c(
                "2",
                f"(couldn't resolve type hints, so no ListNode/TreeNode conversion: {e!r})",
            )
        )
        return {}


def _call_args(
    case: Case, params: list[str], hints: dict[str, object]
) -> tuple[list[object], dict[str, object]]:
    # Copy so in-place solutions can't mutate the test case itself.
    case_args, case_kwargs = copy.deepcopy((case.args, case.kwargs))
    args = [_to_input(a, hints.get(p)) for p, a in zip(params, case_args)]
    args += case_args[len(params) :]
    kwargs = {k: _to_input(v, hints.get(k)) for k, v in case_kwargs.items()}
    return args, kwargs


def _verdict(
    case: Case, got: object, args: list[object], kwargs: dict[str, object]
) -> bool | None:
    """Whether `got` is right, or None when the case has nothing to compare against."""
    if case.check is not None:
        if not _wants_args(case.check):
            return bool(case.check(got))
        after = [_to_plain(a) for a in args]
        after_kw = {k: _to_plain(v) for k, v in kwargs.items()}
        return bool(case.check(got, *after, **after_kw))
    if case.expected is _MISSING:
        return None
    expected = _to_plain(case.expected)
    if case.any_order:
        return _equal(_unordered(got), _unordered(expected))
    return _equal(got, expected)


def _failure_details(
    case: Case, got: object, params: list[str], args: list[object], in_place: bool
) -> list[str]:
    details: list[str] = []
    if case.check is None:
        details.append(f"expected: {_short(_to_plain(case.expected))}")
    details.append(f"got:      {_short(got)}")
    # Show arguments the solution mutated, since a check may depend on them.
    if not in_place:
        for p, before, after in zip(params, case.args, args):
            if not _equal(_to_plain(after), before):
                details.append(f"{p} after: {_short(_to_plain(after))}")
    return details


def _run_case(
    solution: type,
    name: str,
    case: Case,
    params: list[str],
    hints: dict[str, object],
) -> _Outcome:
    label = ", ".join(
        [f"{p}={_short(a, _ARG_LIMIT)}" for p, a in zip(params, case.args)]
        + [f"{k}={_short(v, _ARG_LIMIT)}" for k, v in case.kwargs.items()]
    )
    args, kwargs = _call_args(case, params, hints)
    try:
        start = time.perf_counter()
        instance = cast(object, solution())
        method = cast(Callable[..., object], getattr(instance, name))
        got = method(*args, **kwargs)
        elapsed = time.perf_counter() - start
    except Exception as e:  # noqa: BLE001
        return _Outcome(label, ok=False, error=e)

    # Methods annotated `-> None` work in place: their result is the first argument.
    in_place = "return" in hints and hints["return"] is type(None)
    if in_place:
        got = args[0] if args else next(iter(kwargs.values()), None)
    got = _to_plain(got, hints.get("return"))

    ok = _verdict(case, got, args, kwargs)
    if ok is None:
        details = [f"got:      {_short(got)}"]
    elif ok:
        details = []
    else:
        details = _failure_details(case, got, params, args, in_place)
    return _Outcome(label, ok, elapsed, details=details)


def run(
    solution: type | None = None,
    tests: list[Case] | None = None,
    *,
    method: str | None = None,
) -> None:
    """Run `tests` against `solution`. Both default to `Solution` / `tests` in the calling file.

    The method under test is the first public method on the class unless `method` is given.
    Arguments are converted to ListNode/TreeNode based on the method's type hints, and
    ListNode/TreeNode results are converted back to lists before comparing.
    Methods annotated `-> None` are treated as in-place: the first argument is checked.
    """
    caller: dict[str, Any] = sys._getframe(1).f_globals  # pyright: ignore[reportPrivateUsage, reportExplicitAny]
    solution = solution or cast(type, caller["Solution"])
    tests = tests if tests is not None else cast(list[Case], caller.get("tests", []))
    name = _pick_method(solution, method)

    unbound = cast(Callable[..., object], getattr(solution, name))
    hints = _type_hints(unbound)
    # FORWARDREF: only parameter names are needed, so don't let a bad hint raise.
    signature = inspect.signature(
        unbound, annotation_format=annotationlib.Format.FORWARDREF
    )
    params = list(signature.parameters)[1:]  # drop self

    outcomes = (_run_case(solution, name, case, params, hints) for case in tests)
    if not _run_cases(f"{solution.__name__}.{name}", len(tests), outcomes):
        sys.exit(1)


# --- run_design -----------------------------------------------------------------


def _run_design_case(
    cls: type | None, caller: dict[str, object], case: Case
) -> _Outcome:
    try:
        ops, op_args = cast(tuple[list[str], list[list[object]]], case.args)
        target = cls or cast(type, caller[ops[0]])
    except (ValueError, IndexError, KeyError) as e:
        e.add_note("design cases look like test([ops...], [args...], expected=[...])")
        return _Outcome("malformed case", ok=False, error=e)
    label = f"{len(ops)} ops"

    raw: list[object] = []
    try:
        start = time.perf_counter()
        obj = cast(object, target(*op_args[0]))
        raw.append(None)
        for op, a in zip(ops[1:], op_args[1:]):
            raw.append(cast(Callable[..., object], getattr(obj, op))(*a))
        elapsed = time.perf_counter() - start
    except Exception as e:  # noqa: BLE001
        got_so_far = [_to_plain(r) for r in raw]
        label = f"after {len(raw)} ops, got so far: {_short(got_so_far)}"
        return _Outcome(label, ok=False, error=e)
    got = [_to_plain(r) for r in raw]

    if case.expected is _MISSING:
        return _Outcome(label, None, elapsed, details=[f"got:      {_short(got)}"])
    expected = cast(list[object], case.expected)
    if _equal(got, expected):
        return _Outcome(label, True, elapsed)

    for j, (op, a, e, r) in enumerate(zip(ops, op_args, expected, got)):
        if not _equal(e, r):
            details = [
                f"first mismatch at op #{j}: {op}({_short(a, _OP_ARG_LIMIT)[1:-1]})",
                f"expected: {_short(e)}",
                f"got:      {_short(r)}",
            ]
            break
    else:
        details = [f"expected {len(expected)} results, got {len(got)}"]
    return _Outcome(label, False, elapsed, details=details)


def run_design(cls: type | None = None, tests: list[Case] | None = None) -> None:
    """Run LeetCode "design" problems (LRUCache, MinStack, ...).

    Each case uses LeetCode's format:
        test(["LRUCache", "put", "get"], [[2], [1, 1], [1]], expected=[None, None, 1])
    `cls` defaults to the class named by the first operation in the calling file.
    """
    caller: dict[str, Any] = sys._getframe(1).f_globals  # pyright: ignore[reportPrivateUsage, reportExplicitAny]
    tests = tests if tests is not None else cast(list[Case], caller.get("tests", []))
    for case in tests:
        if case.check is not None or case.any_order:
            raise ValueError("run_design doesn't support check= or any_order=")

    if cls is not None:
        title = cls.__name__
    else:
        # The class named by the first case's constructor op, if it has one.
        first = cast(tuple[list[object], ...], tests[0].args) if tests else ()
        title = str(first[0][0]) if first and first[0] else "design"
    outcomes = (_run_design_case(cls, caller, case) for case in tests)
    if not _run_cases(title, len(tests), outcomes):
        sys.exit(1)
