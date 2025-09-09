# main.py (excerpt)
import time
from TagReader import TagReader

reader = TagReader()
reader.repeat_ms = 0          # don't de-dupe in software while testing cadence
FORCE_RESET_HZ = 10          # docs example: up to ~4 resets/sec
period_ms = int(1000 / FORCE_RESET_HZ)
next_reset_ms = int(time.monotonic() * 1000)

t0 = time.monotonic()
last_hit = None
while time.monotonic() - t0 < 60:  # run 10s test
    now_ms = int(time.monotonic() * 1000)

    # fixed-interval reset (even if nothing was read)
    if now_ms >= next_reset_ms:
        reader.reset()
        next_reset_ms += period_ms

    pkt = reader.poll()  # your existing non-blocking read/parse
    if pkt:              # same tag will show repeatedly if module cooperates
        now = time.monotonic()
        if last_hit is not None:
            print("Δt = {:.3f}s".format(now - last_hit), pkt['id_hex'])
        last_hit = now

    time.sleep(0.005)

