import board
import busio
import time

class MyBT:
    def __init__(self, baudrate=9600, buffer_size=64, timeout=0.2, eom_char='*', tx_chunk=64, add_crlf=False):
        """
        UART Bluetooth helper with non-blocking poll() and bounded receive().

        :param baudrate: UART baudrate (default 9600).
        :param buffer_size: Max bytes to read per poll (default 64).
        :param timeout: Default max seconds for receive(); keep small for snappy loops.
        :param eom_char: End-of-message delimiter (default '*').
        :param tx_chunk: Max bytes per write() call (some modules prefer small frames).
        :param add_crlf: If True, append '\r\n' after the EOM (helps terminal apps show lines).
        """
        self.uart = busio.UART(board.TX, board.RX, baudrate=baudrate)
        self.buffer_size = int(buffer_size)
        self.eom_char = eom_char
        self._buffer = ""     # accumulates partial text between polls
        self.timeout = float(timeout)
        self.tx_chunk = int(tx_chunk)
        self.add_crlf = bool(add_crlf)

    # ---------- Sending ----------
    def _write_chunked(self, b: bytes):
        """Write bytes in small chunks; return total bytes written (or 0/None)."""
        total = 0
        for i in range(0, len(b), self.tx_chunk):
            n = self.uart.write(b[i:i+self.tx_chunk])
            if n is None:
                # Some CircuitPython builds return None; treat as full chunk written
                n = min(self.tx_chunk, len(b) - i)
            total += n
            # tiny pacing helps some bridges
            time.sleep(0.001)
        return total

    def send(self, message: str):
        """
        Send a string with EOM appended if missing.
        Returns number of bytes written (best-effort).
        """
        if not isinstance(message, str):
            raise ValueError("Message must be a string.")
        if not message.endswith(self.eom_char):
            message += self.eom_char
        if self.add_crlf:
            message += "\r\n"
        return self._write_chunked(message.encode("utf-8"))

    def send_line(self, message: str):
        """Convenience: always terminate with EOM + CRLF for terminals."""
        if not message.endswith(self.eom_char):
            message += self.eom_char
        message += "\r\n"
        return self._write_chunked(message.encode("utf-8"))

    def send_bytes(self, payload: bytes):
        """Send raw bytes exactly as given (no EOM/CRLF)."""
        if not isinstance(payload, (bytes, bytearray)):
            raise ValueError("send_bytes expects bytes/bytearray")
        return self._write_chunked(bytes(payload))

    # ---------- Non-blocking receive ----------
    def available(self):
        """Return how many bytes are queued (0 if attribute not supported)."""
        return int(getattr(self.uart, "in_waiting", 0) or 0)

    def read_raw(self, n=None):
        """Read up to n bytes raw (no decode). If n is None, read what's available up to buffer_size."""
        n_avail = self.available()
        if n is None:
            n = min(n_avail, self.buffer_size)
        if n <= 0:
            return b""
        data = self.uart.read(n)  # non-blocking; bytes or None
        return data or b""

    def poll(self):
        """
        Non-blocking check: read whatever bytes are currently available once,
        update internal buffer, and return ONE complete message if present.
        Returns None if no complete message yet.
        """
        raw = self.read_raw()
        if raw:
            # Try utf-8 first; if split multibyte occurred, fall back to lenient per-byte merge
            try:
                self._buffer += raw.decode("utf-8")
            except UnicodeError:
                self._buffer += "".join(chr(b) if 32 <= b < 127 else "?" for b in raw)

        # Parse out exactly one message, if delimiter present
        if self.eom_char in self._buffer:
            msg, remainder = self._buffer.split(self.eom_char, 1)
            self._buffer = remainder
            return msg.strip()
        return None

    def receive(self, timeout=None):
        """
        Bounded wait using repeated poll() calls.
        Returns a message string or None on timeout.
        """
        if timeout is None:
            timeout = self.timeout
        t0 = time.monotonic()
        while True:
            msg = self.poll()
            if msg is not None:
                return msg
            if (time.monotonic() - t0) >= timeout:
                return None
            # Tiny yield to avoid starving the rest of the system
            time.sleep(0.001)

    def send_and_receive(self, message, timeout=None):
        """Send then wait (bounded) for a reply."""
        self.send(message)
        return self.receive(timeout=timeout)

    # ---------- Utilities ----------
    def clear_buffer(self):
        """Drop any partial (unsentinel'd) bytes we've accumulated."""
        self._buffer = ""

    def flush_input(self):
        """Purge anything currently queued in the UART RX FIFO."""
        n_avail = self.available()
        if n_avail:
            _ = self.uart.read(n_avail)
