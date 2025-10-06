import board
import busio
import time

class MyBT:
    def __init__(self, baudrate=9600, buffer_size=64, timeout=0.2, eom_char='*'):
        """
        UART Bluetooth helper with non-blocking poll() and bounded receive().

        :param baudrate: UART baudrate (default 9600).
        :param buffer_size: Max bytes to read per poll (default 64).
        :param timeout: Default max seconds for receive(); keep small for snappy loops.
        :param eom_char: End-of-message delimiter (default '*').
        """
        # NOTE: On CircuitPython, read() is non-blocking; in_waiting tells how many bytes are queued.
        # If your CP version supports it, you can also pass timeout=0 to UART() ctor; not required here.
        self.uart = busio.UART(board.TX, board.RX, baudrate=baudrate)
        self.buffer_size = buffer_size
        self.eom_char = eom_char
        self._buffer = ""     # accumulates partial text between polls
        self.timeout = timeout

    # ---------- Sending ----------
    def send(self, message: str):
        """Send a string with EOM appended if missing."""
        if not isinstance(message, str):
            raise ValueError("Message must be a string.")
        if not message.endswith(self.eom_char):
            message += self.eom_char
        self.uart.write(message.encode("utf-8"))

    # ---------- Non-blocking receive ----------
    def poll(self):
        """
        Non-blocking check: read whatever bytes are currently available once,
        update internal buffer, and return ONE complete message if present.
        Returns None if no complete message yet.
        """
        # Read exactly what's queued, but cap to buffer_size for fairness.
        n_avail = getattr(self.uart, "in_waiting", 0) or 0  # works on CP 7/8+
        if n_avail:
            n_read = min(n_avail, self.buffer_size)
            raw = self.uart.read(n_read)  # non-blocking; returns bytes or None
            if raw:
                # Avoid decode errors from split multibyte sequences
                try: self._buffer += raw.decode("utf-8")
                except UnicodeError: self._buffer += "".join(chr(b) for b in raw if 32 <= b < 127)
               
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
            # (tune down if you need higher loop rate)
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
        # Drain pending bytes once; avoids blocking
        n_avail = getattr(self.uart, "in_waiting", 0) or 0
        if n_avail:
            _ = self.uart.read(n_avail)
