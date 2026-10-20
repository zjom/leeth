"""`from leet import *` gives a solution file the same names LeetCode pre-imports,
plus the test helpers."""

import bisect
import collections
import functools
import heapq
import itertools
import math
import operator
import random
import re
import string
from bisect import bisect_left, bisect_right, insort
from collections import Counter, OrderedDict, defaultdict, deque
from functools import cache, lru_cache, reduce
from heapq import (
    heapify,
    heappop,
    heappush,
    heappushpop,
    heapreplace,
    nlargest,
    nsmallest,
)
from itertools import accumulate, combinations, permutations, product
from math import inf

from icecream import ic

from .runner import run, run_design, test
from .structures import (
    ListNode,
    TreeNode,
    linked_to_list,
    list_to_linked,
    list_to_tree,
    tree_to_list,
)
from .todo import todo

__all__ = [
    "Counter",
    "ListNode",
    "OrderedDict",
    "TreeNode",
    "accumulate",
    # stdlib modules
    "bisect",
    # stdlib names
    "bisect_left",
    "bisect_right",
    "cache",
    "collections",
    "combinations",
    "defaultdict",
    "deque",
    "functools",
    "heapify",
    "heappop",
    "heappush",
    "heappushpop",
    "heapq",
    "heapreplace",
    "ic",
    "inf",
    "insort",
    "itertools",
    "linked_to_list",
    "list_to_linked",
    "list_to_tree",
    "lru_cache",
    "math",
    "nlargest",
    "nsmallest",
    "operator",
    "permutations",
    "product",
    "random",
    "re",
    "reduce",
    # leet
    "run",
    "run_design",
    "string",
    "test",
    "todo",
    "tree_to_list",
]
