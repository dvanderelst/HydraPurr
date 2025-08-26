import time
import board
import busio
from components import MyDigital
from components.MySystemLog import debug, info, warn, error


# --- simple, robust parser ---
def parser_hex_len26(body):
    """
    Parse a 26-character ASCII-hex payload (already after checksum/invert).
    Emits hex, big-endian int, little-endian int, and a stable tag_key.
    Uses only string/ints for maximum CircuitPython compatibility.
    """
    txt = body.decode("ascii").strip()
    up = txt.upper()
    if len(up) != 26:
        return None
    for c in up:
        if c not in "0123456789ABCDEF":
            return None

    # Big-endian integer (as written)
    try:
        id_int_be = int(up, 16)
    except Exception:
        id_int_be = None

    # Little-endian integer (reverse by byte pairs)
    pairs = [up[i:i+2] for i in range(0, len(up), 2)]
    rev_hex = "".join(reversed(pairs))
    try:
        id_int_le = int(rev_hex, 16)
    except Exception:
        id_int_le = None

    return {
        "id_hex": up,
        "id_int_be": id_int_be,
        "id_int_le": id_int_le,
        "tag_key": up,
    }


class TagReader:
    """Cooperative STX/ETX RFID reader with small, focused helpers.
    Emits activity to components.MySystemLog (debug/info/warn/error).
    """

    def __init__(self):
        # pins (fixed defaults)
        self.rx_pin = board.D9
        self.rst_pin = board.D11

        # hardware objects
        self.uart = busio.UART(rx=self.rx_pin, tx=None, baudrate=9600, timeout=0)
        self.rst = MyDigital(self.rst_pin, direction="output")
        self.rst.write(False)

        info("[RFID] init: rx=%s rst=%s baud=9600" % (str(self.rx_pin), str(self.rst_pin)))

        # defaults
        self.buf = bytearray()
        self.max_len = 64
        self.repeat_ms = 500
        self.verbose = False
        self.parser = parser_hex_len26
        self.invert_required = True
        self.stx, self.etx = 0x02, 0x03
        self.last_tag = None
        self.last_ms = 0
        # Reset timing (active-high via transistor)
        self.reset_pulse_ms = 50
        self.reset_settle_ms = 80

    # --- public ---
    def reset(self):
        if not self.rst: return
        debug("[RFID] reset: assert")
        # Assert reset via transistor (gate HIGH pulls module RST to GND)
        self.rst.write(True)
        time.sleep(self.reset_pulse_ms / 1000.0)
        # Release reset (idle LOW on the transistor gate)
        self.rst.write(False)
        debug("[RFID] reset: release; flush UART")
        # Flush UART and parser buffer after reset
        try: n = getattr(self.uart, "in_waiting", 0)
        except AttributeError: n = 0
        if n:
            try:
                _ = self.uart.read(n)
            except Exception as e:
                warn("[RFID] reset: uart flush failed: %r" % (e,))
        self.buf = bytearray()
        # Short settle so the module is ready to speak again
        time.sleep(self.reset_settle_ms / 1000.0)
        debug("[RFID] reset: settled")

    def poll(self):
        """Try to read one RFID frame and return it as dict, or None if not ready.
        Steps:
          1. Read any available UART bytes into buffer.
          2. Look for STX (start marker) in buffer.
          3. If buffer length since STX exceeds max_len → discard and resync.
          4. Look for ETX (end marker) within allowed window.
          5. If no ETX yet → return None (incomplete frame).
          6. Extract frame bytes between STX and ETX.
          7. Validate frame (checksum, invert).
          8. Parse body into dict (via custom parser or default ASCII fallback).
          9. Attach metadata (raw hex, tag_key).
         10. Suppress duplicates within repeat_ms window.
         11. Reset to re‑arm reader, then return packet.
        """
        self.read_buf()
        i = self.find_stx()
        if i < 0:
            return None
        if self.overrun_since(i):
            warn("[RFID] overrun: STX at %d, tail=%d > max_len=%d → resync" % (i, len(self.buf)-i, self.max_len))
            self.discard_through(i)
            return None
        j = self.find_etx_within(i)
        if j < 0:
            return None
        frame = self.extract_frame(i, j)
        body = self.validate_frame(frame)
        if body is None:
            return None
        pkt = self.parse_body(body)
        if pkt is None:
            warn("[RFID] parser returned None; dropping frame")
            return None
        self.attach_meta(pkt, body)
        if not self.dedup(pkt):
            debug("[RFID] duplicate suppressed: %s" % (pkt.get("tag_key"),))
            return None
        info("[RFID] tag: %s" % (pkt.get("tag_key"),))
        # Re‑arm the reader for next read
        self.reset()
        return pkt

    def read_tag(self, timeout_ms=None, sleep_ms=2):
        t0 = int(time.monotonic() * 1000)
        while True:
            pkt = self.poll()
            if pkt:
                return pkt
            if timeout_ms is not None and (int(time.monotonic() * 1000) - t0) >= int(timeout_ms):
                return None
            time.sleep(sleep_ms / 1000.0)

    # --- io/buffer ---
    def read_buf(self):
        try:
            n = getattr(self.uart, "in_waiting", 0)
        except AttributeError:
            n = 0
        if not n:
            return
        chunk = self.uart.read(n)
        if not chunk:
            return
        self.buf.extend(chunk)
        debug("[RFID] read %dB → buf=%dB" % (len(chunk), len(self.buf)))
        if len(self.buf) > self.max_len:
            self.trim_buf()

    def trim_buf(self):
        self.buf = bytearray(self.buf[-self.max_len:])

    def find_stx(self):
        try:
            return self.buf.index(bytes([self.stx]))
        except ValueError:
            if len(self.buf) > self.max_len:
                self.trim_buf()
            return -1

    def overrun_since(self, i):
        return (len(self.buf) - i) > self.max_len

    def find_etx_within(self, i):
        # inclusive window so ETX at i+max_len is allowed
        stop = min(len(self.buf), i + self.max_len) + 1
        try:
            return self.buf.index(bytes([self.etx]), i + 1, stop)
        except ValueError:
            return -1

    def extract_frame(self, i, j):
        frame = bytes(self.buf[i:j + 1])
        # CircuitPython bytearray may not support slice deletion; reassign instead
        self.buf = bytearray(self.buf[j + 1:])
        return frame

    # --- validation/parsing ---
    def validate_frame(self, frame):
        if not frame or frame[0] != self.stx or frame[-1] != self.etx:
            return None
        payload = frame[1:-1]
        if len(payload) < 2:
            return None
        body, csum, inv = payload[:-2], payload[-2], payload[-1]
        x = 0
        for b in body:
            x ^= b
        if x != csum:
            warn("[RFID] checksum mismatch calc=%d pkt=%d" % (x, csum))
            return None
        if self.invert_required and ((csum ^ inv) != 0xFF):
            warn("[RFID] checksum invert mismatch: csum=%d inv=%d" % (csum, inv))
            return None
        return body

    def parse_body(self, body):
        if self.parser:
            try:
                out = self.parser(body)
                if out:
                    return out
                else:
                    warn("[RFID] parser returned None")
            except Exception as e:
                error("[RFID] parser error: %r" % (e,))
                return None
        try:
            txt = body.decode("ascii").strip()
        except Exception:
            txt = ""
        return {"id_ascii": (txt or None)}

    def attach_meta(self, pkt, body):
        pkt["raw_hex"] = body.hex().upper()
        if "tag_key" not in pkt:
            # prefer structured id if provided by parser
            pkt["tag_key"] = pkt.get("card_number") or pkt.get("id_hex") or pkt.get("id_ascii") or pkt["raw_hex"]

    # --- dedup ---
    def dedup(self, pkt):
        now_ms = int(time.monotonic() * 1000)
        key = pkt.get("tag_key")
        if key == self.last_tag and (now_ms - self.last_ms) < self.repeat_ms:
            return False
        self.last_tag, self.last_ms = key, now_ms
        return True

    # --- resync helpers ---
    def discard_through(self, i):
        # Drop up to and including position i; reassign to stay portable
        self.buf = bytearray(self.buf[i + 1:])
        if len(self.buf) > self.max_len:
            self.trim_buf()



