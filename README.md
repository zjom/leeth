# leeth

local leetcode harness to maximise efficiency

- Problem scaffolding
- Run & edit most recently modified file
- Custom validation functions
- Supports LeetCode design questions
- Paste LeetCode inputs as-is: `[1, 2, 3]` becomes a `ListNode` or `TreeNode` when the type hint asks for one
- LeetCode's default imports, plus `ic` and `todo()`
- Colored PASS/FAIL output with diffs and timings

## Install

Requires Python 3.14+.

```sh
uv tool install leeth     # or: pipx install leeth
```

## Workflow

```sh
leeth new 1 two sum            # -> problems/0001_two_sum.py
leeth new https://leetcode.com/problems/two-sum/
leeth new 146 lru cache -d     # design problem

leeth e                        # edit the last-edited problem
leeth                           # run it
leeth run 1                    # run by number or part of the name
```

## Solution file

```python
from leeth import *


class Solution:
    def twoSum(self, nums: list[int], target: int) -> list[int]:
        seen = {}
        for i, n in enumerate(nums):
            if target - n in seen:
                return [seen[target - n], i]
            seen[n] = i


tests = [
    test([2, 7, 11, 15], 9, expected=[0, 1]),
    test(nums=[3, 3], target=6, expected=[1, 0]),
    test([3, 2, 4], 6, expected=[2, 1], any_order=True),
    test([1, 2], 3),  # no expected: just print
]

if __name__ == "__main__":
    run()
```

```
$ leeth
Solution.twoSum  (4 cases)
PASS #1  nums=[2, 7, 11, 15], target=9  0.01 ms
FAIL #2  nums=[3, 3], target=6  0.00 ms
     expected: [1, 0]
     got:      [0, 1]
PASS #3  nums=[3, 2, 4], target=6  0.00 ms
OUT  #4  nums=[1, 2], target=3  0.00 ms
     got:      [0, 1]

2/3 passed  (0.02 ms total)
```

### More test options

```python
# several valid answers / mutated input: check gets the result (+ args after the call)
test([3, 2, 2, 3], 3, check=lambda k, nums, val: sorted(nums[:k]) == [2, 2])

# `-> None` methods: the first argument is compared to expected
test([1, 2, 3], expected=[3, 2, 1])

# pick a method other than the first one
run(method="twoSumSorted")
```

### Design problems

```python
tests = [
    test(["LRUCache", "put", "get"], [[2], [1, 1], [1]], expected=[None, None, 1]),
]

if __name__ == "__main__":
    run_design()
```
