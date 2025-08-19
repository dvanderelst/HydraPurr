import time, binascii
import board, busio, digitalio

class MyRFID:
    def __init__(self, rx_pin=board.D9, reset_pin=board.D11, active_high_reset=True, buf=1024):
        self.rx_pin = rx_pin
        self.buf = buf

        # Reset control (your wiring: HIGH = reset)
        self.rst = digitalio.DigitalInOut(reset_pin)
        self.rst.direction = digitalio.Direction.OUTPUT
        self.active_high_reset = active_high_reset
        self.rst.value = not self.active_high_reset  # idle: not in reset

        self.uart = None

    # --- UART open/close ---
    def _open_uart(self, baud, parity=None, bits=8, timeout=0.02):
        if self.uart is not None:
            try: self.uart.deinit()
            except Exception: pass
            self.uart = None
            time.sleep(0.01)
        self.uart = busio.UART(
            tx=None, rx=self.rx_pin, baudrate=baud,
            timeout=timeout, receiver_buffer_size=self.buf,
            parity=parity, bits=bits
        )

    def _close_uart(self):
        if self.uart is not None:
            try: self.uart.deinit()
            except Exception: pass
            self.uart = None

    # --- Reset pulse ---
    def reset_pulse(self, ms=60, settle_ms=300):
        self.rst.value = True if self.active_high_reset else False
        time.sleep(ms/1000)
        self.rst.value = False if self.active_high_reset else True
        time.sleep(settle_ms/1000)

    # --- RX idle check (UART should idle HIGH) ---
    def rx_idle_high(self):
        # release UART and sample as input w/o pull
        self._close_uart()
        pin = digitalio.DigitalInOut(self.rx_pin)
        pin.direction = digitalio.Direction.INPUT
        pin.pull = None
        time.sleep(0.01)
        level = pin.value
        pin.deinit()
        print(f"[idle] RX is {'HIGH' if level else 'LOW'}")
        return level

    # --- quick sniff ---
    def sniff(self, duration=2.0, show_first=True):
        start = time.monotonic()
        collected = bytearray()
        while time.monotonic() - start < duration:
            n = self.uart.in_waiting
            if n:
                data = self.uart.read(n) or b""
                if data:
                    if show_first:
                        print("RX:", data, "| HEX:", binascii.hexlify(data))
                        show_first = False
                    collected.extend(data)
            time.sleep(0.005)
        return bytes(collected)

    # --- simple line read ---
    def read_line(self, duration=1.5):
        end = time.monotonic() + duration
        while time.monotonic() < end:
            line = self.uart.readline()
            if line:
                print("LINE:", line, "| HEX:", binascii.hexlify(line))
                return bytes(line)
            time.sleep(0.005)
        return b""

    # --- config scanner: tries multiple baud/parity/bits combos ---
    def scan_configs(self, tag_present_hint=True):
        combos = []
        # Common bauds to try
        for b in (9600, 19200, 38400, 57600, 115200, 4800, 2400):
            combos.append((b, None, 8, "8N1"))
            combos.append((b, busio.UART.Parity.EVEN, 7, "7E1"))  # some readers use this
        results = []
        print("Pulsing reset…")
        self.reset_pulse(ms=60, settle_ms=300)
        for baud, parity, bits, label in combos:
            print(f"\n== Trying {baud} {label} ==")
            self._open_uart(baud=baud, parity=parity, bits=bits, timeout=0.02)
            raw = self.sniff(duration=2.0)              # show first packet if any
            line = self.read_line(duration=1.0)
            results.append((baud, label, len(raw), len(line)))
            print(f"-> bytes={len(raw)} lines={'1' if line else '0'}")
        self._close_uart()
        print("\nSummary (baud,mode,bytes,lines):")
        for r in results:
            print(r)
        return results

# ---- run ----
if __name__ == "__main__":
    r = MyRFID(rx_pin=board.D9, reset_pin=board.D11, active_high_reset=True)

    # 1) Electrical sanity: should print HIGH
    r.rx_idle_high()

    # 2) Keep a tag on the antenna continuously during this scan
    results = r.scan_configs()

    # If any row shows bytes > 0 or lines = 1, that (baud, mode) is your winner.
