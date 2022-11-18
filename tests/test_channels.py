def test_channel():
    import random
    import time

    import tqdm

    chan = Channel(out_size=4096, loopback=True)

    nwrite = 0
    nread = 0

    for i in tqdm.tqdm(range(int(10)), smoothing=0.01, unit="byte"):
        data = random.randint(0, 255)
        chan.write_byte(data.to_bytes(1, "little"))

        nwrite += 1

        if random.random() > 0.9:
            out = chan.read_bytes()
            # print(f'read {len(out)} items')
            nread += len(out)

        print(f"current length: {len(chan.in_buffer)}")

    out = chan.read_bytes()
    nread += len(out)

    print(f"\nwrote {nwrite:9,d} items")
    print(f" read {nread:9,d} items")
