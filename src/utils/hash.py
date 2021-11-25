import hashlib
from typing import Union
from .conversions import str_to_bytes, to_bytes


HashInput = Union[str, bytes, bytearray]


def get_blake2b_hash(data: HashInput, digest_size_bytes: int, return_type: str='bytes') -> :
    data = to_bytes(data)
    digest = hashlib.blake2b(data, digest_size=digest_size_bytes).digest()
    if return_type == 'hex':
        return digest.hex()
    return digest


def get_fletcher32_checksum(data: HashInput, return_type: str='bytes'):
    a = to_bytes(data)
    b = [sum(a[:i]) % 65535 for i in range(len(a) + 1)]
    checksum = (sum(b) << 16) | max(b)
    checksum = (checksum).to_bytes(4, byteorder='little')
    if return_type == 'hex':
        return checksum.hex()
    return checksum
