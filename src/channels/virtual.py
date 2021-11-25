from ..buffers.linked_list import FIFOLinkedList
from typing import Any

class VirtualChannel():
    def __init__(self, out_size: int = 4096, in_size: int = 4096, loopback: bool = False) -> None:
        super().__init__()
        self.loopback = loopback
        self.out_buffer = FIFOLinkedList(out_size)

        if loopback:
            self.in_buffer = self.out_buffer
        else:
            self.in_buffer = FIFOLinkedList(in_size)

    def write_bytes(self, data) -> None:
        for char in data:
            self.write_byte(char)

    def write_byte(self, char) -> None:
        self.out_buffer.push(char)

    def read_bytes(self) -> list:
        out = []
        while self.in_buffer.has_data():
            out.append(self.read_byte())
        return out

    def read_byte(self) -> Any:
        return self.in_buffer.pop()
