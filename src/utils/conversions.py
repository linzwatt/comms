from typing import Union


def to_bytes(data: Union[str, bytes, bytearray]):
    if isinstance(data, str):
        return str_to_bytes(data)
    return data


def str_to_bytes(str, encoding="utf-8"):
    return bytes(str, encoding)


def bytes_to_str(b, encoding="utf-8"):
    return b.decode(encoding)
