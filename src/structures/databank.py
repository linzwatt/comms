from typing import Any, Dict

from ..channels.virtual import VirtualChannel
from ..protocols.mailperson import MailPerson
from ..utils.schema import parse_dtype
from .hash_table import HashTable


def flatten_dict(d, parent_key=None) -> Dict:
    items = []
    for key, value in d.items():
        new_key = f"{parent_key}.{key}" if parent_key is not None else key
        if isinstance(value, dict):
            items.extend(flatten_dict(value, new_key).items())
        else:
            items.append((new_key, value))
    return dict(items)


class DataItem:
    def __init__(self, key, dtype, value=None) -> None:
        self.key = key
        self.dtype = parse_dtype(dtype)
        self.value = value
        self.changed = False

    def set(self, new_value):
        self.value = new_value
        self.changed = True

    def get(self):
        return self.value


class DataBank:
    def __init__(self, schema, key_size_bytes) -> None:
        self.schema = flatten_dict(schema)

        self.hash_table: Dict[str, DataItem] = HashTable(
            init_dict={key: DataItem(key, dtype) for key, dtype in self.schema.items()}, key_size_bytes=key_size_bytes
        )

        self.channel = VirtualChannel(loopback=True)
        self.protocol = MailPerson(device_size=2, hash_size=key_size_bytes)

    def set(self, key: str, value: Any):
        self.hash_table[key].set(value)

    def get(self, key: str):
        return self.hash_table[key].get()

    def send(self):
        for key, item in self.hash_table.items():
            if item.changed:
                message = self.protocol.encode_message("00", key, item.dtype, item.value)
                self.channel.write_bytes(message)
                item.changed = False

    def receive(self):
        message = self.protocol.decode_message(self.channel.in_buffer, self.hash_table)
        return message
