from typing import Any, Dict, Optional, Union
import hashlib
import time


schemas = {
    '00': {
        'control': {
            'position': 'int',
            'velocity': 'int',
            'estop': 'int'
        },
        'feedback': {
            'position': 'int',
            'velocity': 'int',
            'status': 'int'
        },
        'info': {
            'firmware_version': 'str'
        }
    }
}


def flatten_dict(d, parent_key=None) -> Dict:
    items = []
    for key, value in d.items():
        new_key = f'{parent_key}.{key}' if parent_key is not None else key
        if isinstance(value, dict):
            items.extend(flatten_dict(value, new_key).items())
        else:
            items.append((new_key, value))
    return dict(items)



class DataItem():
    def __init__(self, key, type, value=None) -> None:
        self.key = key
        self.type = type
        self.value = value
        self.changed = False

    def set(self, new_value):
        self.value = new_value
        self.changed = True

    def get(self):
        return self.value


class DataBank():
    def __init__(self, schema) -> None:
        self.schema = flatten_dict(schema)

        self.hash_table: Dict[str, DataItem] = HashTable(
            init_dict={key: DataItem(key, dtype) for key, dtype in self.schema.items()}
        )

        self.channel = Channel(loopback=True)

    def set(self, key: str, value: Any):
        self.hash_table[key].set(value)

    def get(self, key: str):
        return self.hash_table[key].get()

    def step(self):
        for key, item in self.hash_table.items():
            if item.changed:
                message = encode_message('00', key, item.type, item.value)
                self.channel.write_bytes(message)

        while True:
            message = decode_message(self.channel.in_buffer, self.hash_table)
            print(message)
            if message is None:
                break


def Fletcher32(string):
    a = list(map(ord, string))
    b = [sum(a[:i]) % 65535 for i in range(len(a) + 1)]
    return (sum(b) << 16) | max(b)


def encode_message(device, hash, dtype, data):

    if dtype == 'int':
        data = bytes([data])

    device = bytes(device, 'utf-8')
    hash = bytes(hash, 'utf-8')
    dtype = bytes(dtype, 'utf-8')

    payload = device + hash + data

    header = bytes('bork', 'utf-8')
    checksum = Fletcher32(payload.decode('utf-8'))
    checksum = (checksum).to_bytes(4, byteorder='little')

    return header + payload + checksum


# TODO:
#   - encode values properly - work in bytes - bork -> literal array of bytes etc
#   - make hash table use the actual hex representation instead of hex-chars or whatever


def decode_message(buffer, hash_table, device_size=2, hash_size=4, checksum_size=4, timeout=0.25):
    header = 'bork'

    index = 0
    data_size = 0
    device = bytearray()
    hash = bytearray()
    data = bytearray()
    checksum = bytearray()

    start = time.perf_counter()

    while True:
        found = False
        reset = False
        item = buffer.peek(index)

        if item is None:
            continue

        char = item.item

        # header
        if index < len(header):
            if (char == ord(header[index])):
                index += 1
            else:
                reset = True

        # device
        elif index < len(header) + device_size:
            device.append(char)
            index += 1

        # item hash (n-1) bytes
        elif index < len(header) + device_size + hash_size - 1:
            hash.append(char)
            index += 1

        # item hash last byte / data size
        elif index < len(header) + device_size + hash_size:
            hash.append(char)
            test_dsize = hash_table.get(hash.decode('utf-8'), None)
            if test_dsize is not None:
                data_size = test_dsize
                index += 1
            else:
                reset = True

        # data
        elif index < len(header) + device_size + hash_size + data_size:
            data.append(char)
            index += 1

        # checksum
        elif index < len(header) + device_size + hash_size + data_size + checksum:
            checksum.append(char)
            index += 1

        # check checksum
        else:
            test_checksum = Fletcher32(device.extend(hash).extend(data))
            if checksum == test_checksum:
                found = True
            else:
                reset = True

        if reset:
            for _ in range(index + 1):
                buffer.pop()
            index = 0
            data_size = 0
            device = bytearray()
            hash = bytearray()
            data = bytearray()
            checksum = bytearray()

        if found:
            for _ in range(index):
                buffer.pop()
            return (device, hash, data)

        # if time.perf_counter() - start > timeout:
        #     return None

class HashTable(dict):
    def __init__(self, init_dict: Dict[str, Any] = {}, key_size_bytes: int = 4) -> None:
        self.key_size_bytes = key_size_bytes

        for key, value in init_dict.items():
            self[key] = value

    def hash(self, key: str) -> str:
        return hashlib.blake2b(bytes(key, 'utf-8'), digest_size=self.key_size_bytes).hexdigest()

    def __setitem__(self, key, value) -> None:
        dict.__setitem__(self, self.hash(key), value)

    def __getitem__(self, key) -> Any:
        return dict.__getitem__(self, self.hash(key))


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


class Channel():
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


def test_channel():
    import time
    import tqdm
    import random

    chan = Channel(out_size = 4096, loopback=True)

    nwrite = 0
    nread = 0

    for i in tqdm.tqdm(range(int(10)), smoothing=0.01, unit='byte'):
        data = random.randint(0, 255)
        chan.write_byte(data.to_bytes(1, 'little'))

        nwrite += 1

        if random.random() > 0.9:
            out = chan.read_bytes()
            # print(f'read {len(out)} items')
            nread += len(out)

        print(f'current length: {len(chan.in_buffer)}')

    out = chan.read_bytes()
    nread += len(out)

    print(f'\nwrote {nwrite:9,d} items')
    print(f' read {nread:9,d} items')


if __name__ == "__main__":

    # test_channel()

    db = DataBank(schemas['00'])

    db.set('control.position', 69)
    db.set('control.velocity', 38)

    db.step()

    out = db.channel.read_bytes()
    print(bytes(out))
