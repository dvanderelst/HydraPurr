# TagReader.py — cooperative, scheduled-reset RFID reader (hardcoded settings)

import time
import board
import busio
from components import MyDigital
from components.MySystemLog import debug, info, warn, error

# --- simple, robust parser for 26-char ASCII hex payloads --------------------
def parser_hex_len26(body: bytes):
    """
    Parse a 26-character ASCII-hex payload (already after checksum/invert).
    Returns fields: tag (26-char hex), id_int_be, id_int_le, tag_key (same hex).
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
        "tag": up,
        "id_int_be": id_int_be,
        "id_int_le": id_int_le,
        "tag_key": up,
    }


class TagReader:
    """
    STX/ETX framed RFID reader for WL-134.
    - Non-blocking: poll() never sleeps.
    - Internal fixed-cadence reset (~3 Hz) using a tiny state machine.
    - When a full, valid frame arrives, poll() returns a dict; otherwise None.
    """

    def __init__(self):
        # ---------------- Hardware pins & UART (hardcoded) -------------------
        self.rx_pin = board.D9
        self.rst_pin = board.D11
        self.baudrate = 9600

        # Non-blocking UART (timeout=0)
        self.uart = busio.UART(rx=self.rx_pin, tx=None, baudrate=self.baudrate, timeout=0)

        # Reset transistor: True → assert reset (pull module RST low through transistor)
        self.rst = MyDigital(self.rst_pin, direction="output")
        self.rst.write(False)  # idle (not asserting reset)

        debug(f"[RFID] init: rx={self.rx_pin} rst={self.rst_pin} baud={self.baudrate}")

        # ---------------- Framing & validation (hardcoded) -------------------
        self.stx = 0x02
        self.etx = 0x03
        self.max_len = 64
        self.invert_required = True
        self.parser = parser_hex_len26

        # ---------------- De-dup (ms) ---------------------------------------
        self.repeat_ms = 100
        self.last_tag = None
        self.last_ms = 0

        # ---------------- Scheduled reset (hardcoded cadence) ----------------
        self.reset_pulse_ms = 75     # low pulse duration
        self.reset_settle_ms = 80    # settle after release
        self.force_reset_hz = 3.0    # ~3 Hz matches your measured 2–3 Hz output

        self.period_ms = int(1000 / self.force_reset_hz) if self.force_reset_hz > 0 else 0
        now = self.now_ms()
        self.next_reset_ms = now + self.period_ms if self.period_ms else 0
        self.rst_state = "idle"      # "idle" | "pulsing" | "settling"
        self.rst_until_ms = 0

        # ---------------- Buffers -------------------------------------------
        self.buf = bytearray()

    # ===== tiny helpers (no leading underscores to match your pref) ==========
    def now_ms(self):
        return int(time.monotonic() * 1000)

    # Non-blocking reset state machine
    def tick_reset(self, now_ms: int):
        if self.period_ms and self.rst_state == "idle" and now_ms >= self.next_reset_ms:
            # start pulse (assert reset)
            self.rst.write(True)
            self.rst_state = "pulsing"
            self.rst_until_ms = now_ms + self.reset_pulse_ms
            debug("[RFID] reset: assert")
            return

        if self.rst_state == "pulsing" and now_ms >= self.rst_until_ms:
            # release reset → begin settle
            self.rst.write(False)
            self.rst_state = "settling"
            self.rst_until_ms = now_ms + self.reset_settle_ms
            debug("[RFID] reset: release; settling")
            return

        if self.rst_state == "settling" and now_ms >= self.rst_until_ms:
            # finished; schedule next period (strictly periodic, no drift)
            self.rst_state = "idle"
            if self.period_ms:
                self.next_reset_ms += self.period_ms
            debug("[RFID] reset: settled")
            return

    # Schedule an immediate non-blocking reset (for bench use; no sleeps)
    def reset_now(self):
        t = self.now_ms()
        # If already mid-cycle, let it finish; otherwise start now
        if self.rst_state == "idle":
            self.next_reset_ms = t
            self.tick_reset(t)

    # UART read: never blocks
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
        debug(f"[RFID] read {len(chunk)}B → buf={len(self.buf)}B")
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
        stop = min(len(self.buf), i + self.max_len) + 1
        try:
            return self.buf.index(bytes([self.etx]), i + 1, stop)
        except ValueError:
            return -1

    def extract_frame(self, i, j):
        frame = bytes(self.buf[i:j + 1])
        self.buf = bytearray(self.buf[j + 1:])  # drop consumed bytes
        return frame

    # ===== validation & parsing =============================================
    def validate_frame(self, frame: bytes):
        if not frame or frame[0] != self.stx or frame[-1] != self.etx:
            return None
        payload = frame[1:-1]
        if len(payload) < 2:
            return None
        body, csum, inv = payload[:-2], payload[-2], payload[-1]

        # XOR checksum over body
        x = 0
        for b in body:
            x ^= b
        if x != csum:
            warn(f"[RFID] checksum mismatch calc={x} pkt={csum}")
            return None

        # Invert check (optional)
        if self.invert_required and ((csum ^ inv) != 0xFF):
            warn(f"[RFID] checksum invert mismatch: csum={csum} inv={inv}")
            return None
        return body

    def parse_body(self, body: bytes):
        # Preferred: structured parser
        if self.parser:
            try:
                out = self.parser(body)
                if out:
                    return out
                else:
                    warn("[RFID] parser returned None")
            except Exception as e:
                error(f"[RFID] parser error: {e!r}")
                return None
        # Fallback: raw ASCII (less ideal)
        try:
            txt = body.decode("ascii").strip()
        except Exception:
            txt = ""
        return {"id_ascii": (txt or None), "tag_key": (txt or None)}

    def attach_meta(self, pkt: dict, body: bytes, now_ms: int):
        # raw_hex is hex of the ASCII payload bytes (debug only)
        pkt["raw_hex"] = body.hex().upper()
        if "tag_key" not in pkt:
            pkt["tag_key"] = pkt.get("tag") or pkt.get("id_hex") or pkt.get("id_ascii") or pkt["raw_hex"]
        pkt["time_ms"] = now_ms

    def dedup(self, key: str, now_ms: int) -> bool:
        if key == self.last_tag and (now_ms - self.last_ms) < self.repeat_ms:
            return False
        self.last_tag, self.last_ms = key, now_ms
        return True

    # ===== main entry: non-blocking poll ====================================
    def poll(self):
        """
        Call frequently. Never sleeps.
        Returns a packet dict on a full, valid frame, else None.
        """
        now_ms = self.now_ms()

        # drive the reset cadence (no blocking)
        if self.period_ms:
            self.tick_reset(now_ms)

        # parse at most one frame per call
        self.read_buf()
        i = self.find_stx()
        if i < 0:
            return None
        if self.overrun_since(i):
            warn(f"[RFID] overrun: STX at {i}, tail={len(self.buf)-i} > max_len={self.max_len} → resync")
            # drop through STX to resync next time
            self.buf = bytearray(self.buf[i + 1:])
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
            return None

        self.attach_meta(pkt, body, now_ms)
        key = pkt.get("tag_key")
        if not key:
            return None

        if not self.dedup(key, now_ms):
            debug(f"[RFID] duplicate suppressed: {key}")
            return None

        debug(f"[RFID] tag: {key}")
        return pkt
