"""LeetCode's built-in data structures plus helpers to convert to/from plain lists."""

from collections import deque
from typing import override


class ListNode:
    def __init__(self, val: int = 0, next: ListNode | None = None):
        self.val: int = val
        self.next: ListNode | None = next

    @override
    def __repr__(self) -> str:
        return f"ListNode({linked_to_list(self)})"


class TreeNode:
    def __init__(
        self,
        val: int = 0,
        left: TreeNode | None = None,
        right: TreeNode | None = None,
    ):
        self.val: int = val
        self.left: TreeNode | None = left
        self.right: TreeNode | None = right

    @override
    def __repr__(self) -> str:
        return f"TreeNode({tree_to_list(self)})"


def list_to_linked(values: list[int]) -> ListNode | None:
    """[1, 2, 3] -> 1 -> 2 -> 3"""
    dummy = tail = ListNode()
    for v in values:
        tail.next = ListNode(v)
        tail = tail.next
    return dummy.next


def linked_to_list(head: ListNode | None, limit: int = 10_000) -> list[int | str]:
    """1 -> 2 -> 3 -> [1, 2, 3]. Stops after `limit` nodes to survive cycles."""
    out: list[int | str] = []
    while head is not None and len(out) < limit:
        out.append(head.val)
        head = head.next
    if head is not None:
        out.append("...")
    return out


def list_to_tree(values: list[int | None]) -> TreeNode | None:
    """LeetCode level-order form, e.g. [3, 9, 20, None, None, 15, 7]."""
    if not values or values[0] is None:
        return None
    it = iter(values[1:])
    root = TreeNode(values[0])
    queue = deque([root])
    while queue:
        node = queue.popleft()
        if (v := next(it, None)) is not None:
            node.left = TreeNode(v)
            queue.append(node.left)
        if (v := next(it, None)) is not None:
            node.right = TreeNode(v)
            queue.append(node.right)
    return root


def tree_to_list(root: TreeNode | None) -> list[int | None]:
    """Inverse of list_to_tree, with trailing Nones trimmed."""
    out: list[int | None] = []
    queue: deque[TreeNode | None] = deque([root])
    while queue:
        node = queue.popleft()
        if node is None:
            out.append(None)
            continue
        out.append(node.val)
        queue.append(node.left)
        queue.append(node.right)
    while out and out[-1] is None:
        _ = out.pop()
    return out
