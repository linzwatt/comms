from collections import namedtuple
from pathlib import Path

import yaml


DType = namedtuple("DType", ["dtype", "name", "nbytes"])


def parse_dtype(dtype):
    # TODO: re.match here
    name = dtype.split("(")[0]
    nbytes = int(dtype.split("(")[1].split(")")[0])
    dtype = DType(dtype, name, nbytes)
    return dtype


def clean_path(path):
    return Path(path).expanduser().resolve()


def load_schema(name, root_dir):
    schema_path = clean_path(root_dir) / (name + ".yaml")
    with open(schema_path, "r") as yaml_file:
        schema = yaml.safe_load(yaml_file)
    return schema
