from typing import Any, Dict, Optional, Union
import hashlib
import time
from functools import partial


data_sizes = {
    'int': 1
}


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


if __name__ == "__main__":

    # test_channel()

    import random

    db = DataBank(schemas['00'])

    vars = ['control.position', 'control.velocity', 'control.estop']

    count = 0
    while True:
        var = random.choice(vars)
        n = random.randint(0, 255)
        db.set(var, n)

        if random.random() > 0.75:
            db.channel.write_bytes(bytearray([random.randint(0, 255) for _ in range(random.randint(0, 100))]))

        db.send()

        if random.random() > 0.75:
            db.channel.write_bytes(bytearray([random.randint(0, 255) for _ in range(random.randint(0, 100))]))

        message = db.receive()
        if message is not None:
            device, hash, data = message
            assert n == data
            count += 1
        print(count, len(db.channel.out_buffer))

    # out = db.channel.read_bytes()
    # print(bytes(out))
