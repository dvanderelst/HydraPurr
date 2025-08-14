from adafruit_other import adafruit_ssd1306
from adafruit_other import adafruit_framebuf
import board
import busio

# Module-level constants for display configuration
DEFAULT_WIDTH = 128
DEFAULT_HEIGHT = 64
DEFAULT_SCALE = 1


class MyOLED:
    # Default I2C setup
    def __init__(self, i2c=None, width=DEFAULT_WIDTH, height=DEFAULT_HEIGHT, default_scale=DEFAULT_SCALE):
        if i2c is None:
            scl = board.D13
            sda = board.D12
            i2c = busio.I2C(scl, sda)
        # Initialize the SSD1306 OLED display
        self.oled = adafruit_ssd1306.SSD1306_I2C(width, height, i2c)
        # Create a framebuffer to directly draw on the OLED
        self.framebuffer = adafruit_framebuf.FrameBuffer(self.oled.buffer, width, height, adafruit_framebuf.MVLSB)
        self.default_scale = default_scale  # Set the default text scaling factor
        self.width = width
        self.height = height

    def clear(self):
        """Clear the display."""
        self.oled.fill(0)

    def write(self, text, x, y, scale=None, clear=True):
        """Display scaled text on the OLED, with automatic clear and show."""
        if clear: self.clear()  # Automatically clear the display before writing
        text = str(text)
        # Use the provided scale if given, otherwise use the default scale
        if scale is None: scale = self.default_scale
        char_width = 8 * scale
        char_height = 8 * scale
        # Check if the text fits on the screen
        for i, char in enumerate(text):
            if x + (i * char_width) > self.width or y + char_height > self.height:
                print("Text exceeds display boundaries.")
                return
            self.framebuffer_char_scaled(char, x + i * char_width, y, scale)
        self.oled.show()  # Automatically refresh the display after writing

    def framebuffer_char_scaled(self, char, x, y, scale):
        """Draw a scaled character on the framebuffer."""
        # Create a temporary framebuffer for the 8x8 character
        temp_buffer = bytearray(8 * 8)
        temp_framebuffer = adafruit_framebuf.FrameBuffer(temp_buffer, 8, 8, adafruit_framebuf.MVLSB)
        # Draw the character in its normal 8x8 size
        temp_framebuffer.text(char, 0, 0, 1)
        # Scale up each pixel of the character
        for i in range(8):
            for j in range(8):
                if temp_framebuffer.pixel(i, j):
                    # Scale the pixel for larger sizes
                    for dx in range(scale):
                        for dy in range(scale):
                            # Ensure we stay within display boundaries
                            if (x + i * scale + dx) < self.width and (y + j * scale + dy) < self.height:
                                self.framebuffer.pixel(x + i * scale + dx, y + j * scale + dy, 1)
