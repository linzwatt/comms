from ..utils.hash import get_fletcher32_checksum
from ..utils.sizes import data_sizes
import time


class MailPerson():
    def __init__(self, device_size=2, hash_size=4, header='bork') -> None:
        self.device_size = device_size
        self.hash_size = hash_size
        self.checksum_size = 4
        self.header = header

    def encode_message(self, device, hash, dtype, data):
        if dtype == 'int':
            data = bytes([data])

        device = bytes(device, 'utf-8')
        hash = bytes.fromhex(hash)

        payload = device + hash + data

        header = bytes('bork', 'utf-8')
        checksum = get_fletcher32_checksum(payload)

        return header + payload + checksum

    def _reset_decode(self):
        self._index = 0
        self._data_size = 0
        self._device = bytearray()
        self._hash = bytearray()
        self._data = bytearray()
        self._checksum = bytearray()

    def decode_message(self, buffer, hash_table, timeout=0.25):
        start = time.perf_counter()
        self._reset_decode()

        while True:
            found = False
            reset = False
            item = buffer.peek(self._index)

            if time.perf_counter() - start > timeout:
                return None

            if item is None:
                continue

            char = item.item

            # header
            if self._index < len(self.header):
                if (char == ord(self.header[self._index])):
                    self._index += 1
                else:
                    reset = True

            # device
            elif self._index < len(self.header) + self.device_size:
                self._device.append(char)
                self._index += 1

            # item hash (n-1) bytes
            elif self._index < len(self.header) + self.device_size + self.hash_size - 1:
                self._hash.append(char)
                self._index += 1

            # item hash last byte / data size
            elif self._index < len(self.header) + self.device_size + self.hash_size:
                self._hash.append(char)
                # TODO: add a `get` function to the hash table that handles keyerror, or looks for key in keys() first
                dtype = hash_table.get(hash.hex(), None)
                if dtype is not None:
                    self._data_size = data_sizes.get(dtype.type, None)
                    if self._data_size is not None:
                        self._index += 1
                    else:
                        reset = True
                else:
                    reset = True

            # data
            elif self._index < len(self.header) + self.device_size + self.hash_size + self._data_size:
                self._data.append(char)
                self._index += 1

            # checksum
            elif self._index < len(self.header) + self.device_size + self.hash_size + self._data_size + self.checksum_size:
                self._checksum.append(char)
                self._index += 1

            # check checksum
            else:
                test_checksum = get_fletcher32_checksum(self._device + self._hash + self._data)
                if self._checksum == test_checksum:
                    found = True
                else:
                    reset = True

            if reset:
                for _ in range(self._index + 1):
                    buffer.pop()
                self._reset_decode()

            if found:
                for _ in range(self._index):
                    buffer.pop()
                return (self._device.decode('utf-8'), self._hash.hex(), int.from_bytes(self._data, 'little'))
