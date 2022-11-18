if __name__ == "__main__":

    import random

    from src.structures.databank import DataBank
    from src.utils.schema import load_schema

    schema = load_schema("orion5_v1", "schemas/")

    databank = DataBank(schema, key_size_bytes=4)

    vars_to_change = ["control.position", "control.velocity", "control.estop"]

    count = 0
    while True:
        var = random.choice(vars_to_change)
        n = random.randint(0, 255)
        databank.set(var, n)

        if random.random() > 0.75:
            databank.channel.write_bytes(bytearray([random.randint(0, 255) for _ in range(random.randint(0, 100))]))

        databank.send()

        if random.random() > 0.75:
            databank.channel.write_bytes(bytearray([random.randint(0, 255) for _ in range(random.randint(0, 100))]))

        message = databank.receive()
        if message is not None:
            device, hash, data = message
            assert n == data
            count += 1

        print(count, len(databank.channel.out_buffer))
