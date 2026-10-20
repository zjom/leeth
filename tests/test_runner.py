import pytest

from leet.runner import run, run_design, test
from leet.structures import ListNode, TreeNode


def _run_output(
    capsys: pytest.CaptureFixture[str], *args: object, **kwargs: object
) -> tuple[str, bool]:
    """Call `run` and return (stdout, passed)."""
    try:
        run(*args, **kwargs)  # pyright: ignore[reportArgumentType]
    except SystemExit:
        return capsys.readouterr().out, False
    return capsys.readouterr().out, True


def _design_output(
    capsys: pytest.CaptureFixture[str], *args: object
) -> tuple[str, bool]:
    try:
        run_design(*args)  # pyright: ignore[reportArgumentType]
    except SystemExit:
        return capsys.readouterr().out, False
    return capsys.readouterr().out, True


class TwoSum:
    def twoSum(self, nums: list[int], target: int) -> list[int]:
        seen: dict[int, int] = {}
        for i, n in enumerate(nums):
            if target - n in seen:
                return [seen[target - n], i]
            seen[n] = i
        return []


class Reverse:
    def reverseList(self, head: ListNode | None) -> ListNode | None:
        prev = None
        while head:
            head.next, prev, head = prev, head, head.next
        return prev


class Depth:
    def maxDepth(self, root: TreeNode | None) -> int:
        if root is None:
            return 0
        return 1 + max(self.maxDepth(root.left), self.maxDepth(root.right))


class InPlace:
    def reverseString(self, s: list[str]) -> None:
        s.reverse()


class Floats:
    def values(self, nums: list[float]) -> list[float]:
        return nums


class Boom:
    def solve(self, n: int) -> int:
        return 1 // n


# --- run ----------------------------------------------------------------------


def test_pass_fail_out(capsys: pytest.CaptureFixture[str]) -> None:
    out, passed = _run_output(
        capsys,
        TwoSum,
        [
            test([2, 7, 11, 15], 9, expected=[0, 1]),
            test(nums=[3, 3], target=6, expected=[1, 0]),
            test([1, 2], 3),
        ],
    )
    assert not passed
    lines = out.splitlines()
    assert lines[0] == "TwoSum.twoSum  (3 cases)"
    assert lines[1].startswith("PASS #1  nums=[2, 7, 11, 15], target=9  ")
    assert lines[2].startswith("FAIL #2  nums=[3, 3], target=6  ")
    assert lines[3] == "     expected: [1, 0]"
    assert lines[4] == "     got:      [0, 1]"
    assert lines[5].startswith("OUT  #3  nums=[1, 2], target=3  ")
    assert lines[6] == "     got:      [0, 1]"
    assert "1/2 passed" in out


def test_error_is_reported_and_fails(capsys: pytest.CaptureFixture[str]) -> None:
    out, passed = _run_output(capsys, Boom, [test(0, expected=1), test(1, expected=1)])
    assert not passed
    assert "ERR  #1  n=0" in out
    assert "ZeroDivisionError" in out
    assert "PASS #2  n=1" in out
    assert "1/2 passed" in out


def test_linked_list_conversion(capsys: pytest.CaptureFixture[str]) -> None:
    out, passed = _run_output(
        capsys, Reverse, [test([1, 2, 3], expected=[3, 2, 1]), test([], expected=[])]
    )
    assert passed, out


def test_tree_conversion(capsys: pytest.CaptureFixture[str]) -> None:
    out, passed = _run_output(
        capsys, Depth, [test([3, 9, 20, None, None, 15, 7], expected=3)]
    )
    assert passed, out


def test_in_place_checks_first_argument(capsys: pytest.CaptureFixture[str]) -> None:
    out, passed = _run_output(capsys, InPlace, [test(["a", "b"], expected=["b", "a"])])
    assert passed, out


def test_case_args_are_not_mutated(capsys: pytest.CaptureFixture[str]) -> None:
    case = test(["a", "b"], expected=["b", "a"])
    _ = _run_output(capsys, InPlace, [case])
    assert case.args == (["a", "b"],)


def _is_pair(got: list[int]) -> bool:
    return sorted(got) == [0, 1]


def _sums_to_target(got: list[int], nums: list[int], target: int) -> bool:
    return nums[got[0]] + nums[got[1]] == target


def _has_size(got: list[int], size: int = 2) -> bool:
    return len(got) == size


def test_check_with_and_without_args(capsys: pytest.CaptureFixture[str]) -> None:
    out, passed = _run_output(
        capsys,
        TwoSum,
        [
            test([2, 7], 9, check=_is_pair),
            test([2, 7], 9, check=_sums_to_target),
        ],
    )
    assert passed, out


def test_check_with_default_param_gets_only_result(
    capsys: pytest.CaptureFixture[str],
) -> None:
    out, passed = _run_output(capsys, TwoSum, [test([2, 7], 9, check=_has_size)])
    assert passed, out


def test_any_order(capsys: pytest.CaptureFixture[str]) -> None:
    out, passed = _run_output(
        capsys, TwoSum, [test([2, 7], 9, expected=[1, 0], any_order=True)]
    )
    assert passed, out


def test_any_order_with_close_floats(capsys: pytest.CaptureFixture[str]) -> None:
    out, passed = _run_output(
        capsys, Floats, [test([9.9999999, 10.5], expected=[10.0, 10.5], any_order=True)]
    )
    assert passed, out


def test_method_option(capsys: pytest.CaptureFixture[str]) -> None:
    class Two:
        def first(self) -> int:
            return 1

        def second(self) -> int:
            return 2

    out, passed = _run_output(capsys, Two, [test(expected=2)], method="second")
    assert passed, out
    assert out.startswith("Two.second")


def test_unresolvable_hints_warn(capsys: pytest.CaptureFixture[str]) -> None:
    class Bad:
        def solve(self, x: Missing) -> int:  # pyright: ignore[reportUndefinedVariable, reportUnknownParameterType, reportUnusedParameter]  # noqa: F821
            return 1

    out, passed = _run_output(capsys, Bad, [test(1, expected=1)])
    assert passed, out
    assert "type hints" in out


# What a solution file defines; `run()` with no arguments picks these up.
Solution = TwoSum
tests = [test([2, 7], 9, expected=[0, 1])]


def test_tests_default_to_caller_globals(capsys: pytest.CaptureFixture[str]) -> None:
    run()
    assert "PASS #1" in capsys.readouterr().out


# --- run_design -----------------------------------------------------------------


class Counter:
    def __init__(self, start: int) -> None:
        self.n: int = start

    def inc(self) -> int:
        self.n += 1
        return self.n

    def fail(self) -> int:
        raise RuntimeError("nope")


def test_design_pass_and_mismatch(capsys: pytest.CaptureFixture[str]) -> None:
    out, passed = _design_output(
        capsys,
        Counter,
        [
            test(["Counter", "inc", "inc"], [[0], [], []], expected=[None, 1, 2]),
            test(["Counter", "inc", "inc"], [[0], [], []], expected=[None, 1, 3]),
        ],
    )
    assert not passed
    lines = out.splitlines()
    assert lines[0] == "Counter  (2 cases)"
    assert lines[1].startswith("PASS #1  3 ops  ")
    assert lines[2].startswith("FAIL #2  3 ops  ")
    assert lines[3] == "     first mismatch at op #2: inc()"
    assert lines[4] == "     expected: 3"
    assert lines[5] == "     got:      2"


def test_design_error_mid_sequence(capsys: pytest.CaptureFixture[str]) -> None:
    out, passed = _design_output(
        capsys,
        Counter,
        [test(["Counter", "inc", "fail"], [[0], [], []], expected=[None, 1, 2])],
    )
    assert not passed
    assert "ERR  #1  after 2 ops, got so far: [None, 1]" in out
    assert "RuntimeError: nope" in out


def test_design_out(capsys: pytest.CaptureFixture[str]) -> None:
    out, passed = _design_output(capsys, Counter, [test(["Counter", "inc"], [[5], []])])
    assert passed
    assert "OUT  #1  2 ops" in out
    assert "got:      [None, 6]" in out


def test_design_malformed_case_is_an_error(capsys: pytest.CaptureFixture[str]) -> None:
    out, passed = _design_output(capsys, Counter, [test(["Counter"], expected=[None])])
    assert not passed
    assert "ERR  #1" in out


def test_design_unknown_class_is_an_error(capsys: pytest.CaptureFixture[str]) -> None:
    out, passed = _design_output(capsys, None, [test(["Nope"], [[0]], expected=[None])])
    assert not passed
    assert out.startswith("Nope  (1 case)")
    assert "ERR  #1  malformed case" in out
    assert "KeyError" in out


def test_design_rejects_unsupported_options() -> None:
    with pytest.raises(ValueError, match="any_order"):
        run_design(Counter, [test(["Counter"], [[0]], expected=[None], any_order=True)])


def test_design_empty_prints_header(capsys: pytest.CaptureFixture[str]) -> None:
    out, passed = _design_output(capsys, Counter, [])
    assert passed
    assert out.startswith("Counter  (0 cases)")
