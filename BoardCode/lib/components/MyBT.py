import board
import busio
import time

class MyBT:
    def __init__(self, baudrate=9600, buffer_size=32, timeout=5):
        """
        Initialize the myBT communication object.

        :param baudrate: Baudrate for the UART connection (default is 9600).
        :param buffer_size: Maximum number of bytes to read at a time (default is 32).
        :param timeout: Maximum time (in seconds) to wait for a message (default is 5).
        """
        self.uart = busio.UART(board.TX, board.RX, baudrate=baudrate)
        self.buffer_size = buffer_size
        self.eom_char = '*'  # Hardcoded end-of-message character
        self._buffer = ""
        self.timeout = timeout

    def send(self, message):
        """
        Send a string message over UART.

        :param message: The string message to send.
        """
        if isinstance(message, str):
            if not message.endswith(self.eom_char): message = message + self.eom_char
            self.uart.write(message.encode("utf-8"))  # Encode string to bytes
        else:
            raise ValueError("Message must be a string.")

    def receive(self):
        """
        Receive a message over UART until the end-of-message character is detected or timeout occurs.

        :return: The complete message as a string, or None if no complete message is received before timeout.
        """
        start_time = time.monotonic()  # Record the start time
        while True:
            data = self.uart.read(self.buffer_size)  # Read up to buffer_size bytes
            if data:
                self._buffer += data.decode("utf-8")  # Decode and append to the buffer
                if self.eom_char in self._buffer:  # Check for the EOM character
                    message, self._buffer = self._buffer.split(self.eom_char, 1)
                    return message.strip()
            # Check if timeout has occurred
            if time.monotonic() - start_time > self.timeout:
                return None

    def send_and_receive(self, message):
        """
        Send a message and wait for a complete response or timeout.

        :param message: The string message to send.
        :return: The received response as a string, or None if no response is received before timeout.
        """
        self.send(message)
        return self.receive()
