from typing import Any, Dict, Optional, Union

from ..utils.hash import get_blake2b_hash


class HashTable(dict):
    def __init__(self, init_dict: Dict[str, Any] = {}, key_size_bytes: int = 4) -> None:
        self.key_size_bytes = key_size_bytes

        for key, value in init_dict.items():
            self[key] = value

    def hash(self, key: str) -> str:
        return get_blake2b_hash(key, self.key_size_bytes, "hex")

    def get(self, key: str, default: Optional[Any] = None) -> Union[None, Any]:
        hash = self.hash(key)
        if hash in self.keys():
            return self[hash]
        return default

    def __setitem__(self, key, value) -> None:
        dict.__setitem__(self, self.hash(key), value)

    def __getitem__(self, key) -> Any:
        return dict.__getitem__(self, self.hash(key))
