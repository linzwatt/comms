from typing import Any, Optional, Union

class LinkedListNode():
    def __init__(self, item: Any) -> None:
        self.item = item
        self.next: Node = None

Node = Union[LinkedListNode, None]

class FIFOLinkedList():
    def __init__(self, max_size: Optional[int] = None) -> None:
        self.size = max_size
        self.head: Node = None
        self.tail: Node = None

    def push(self, item) -> None:
        new_node = LinkedListNode(item)

        if self.head is None:
            self.head = new_node
            self.tail = new_node
        else:
            self.head.next = new_node
            self.head = new_node

        self.trim()

    def pop(self) -> Node:
        if self.tail is None:
            return None

        old_tail = self.tail
        self.tail = old_tail.next
        if self.tail is None:
            self.head = None
        return old_tail.item

    def peek(self, i, start=None) -> Node:
        if self.tail is None:
            return None

        if start is None:
            start = self.tail

        if i == 0:
            return start

        if start is None:
            return None

        return self.peek(i-1, start.next)

    def get_last_node(self, start) -> Node:
        if start is None:
            return None
        if start.next is None:
            return start
        return self.get_last_node(start.next)

    def get_length(self, start) -> int:
        if start is None:
            return 0
        return 1 + self.get_length(start.next)

    def has_data(self) -> bool:
        return self.tail is not None

    def trim(self) -> None:
        if self.size is not None:
            while self.get_length(self.tail) > self.size:
                self.pop()

    def __len__(self):
        return self.get_length(self.tail)
