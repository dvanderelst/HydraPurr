import busio
import digitalio
import board
import adafruit_mcp3xxx.mcp3008 as MCP
from adafruit_mcp3xxx.analog_in import AnalogIn
from LickLibrary import Settings


class myAnalog:
    def __init__(self):
        spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)
        cs = digitalio.DigitalInOut(Settings.cs_pin)
        mcp = MCP.MCP3008(spi, cs)
        self.chan0 = AnalogIn(mcp, MCP.P0)
        self.chan1 = AnalogIn(mcp, MCP.P1)
        self.chan2 = AnalogIn(mcp, MCP.P2)
        self.chan3 = AnalogIn(mcp, MCP.P3)
        self.chan4 = AnalogIn(mcp, MCP.P4)
        self.chan5 = AnalogIn(mcp, MCP.P5)
        self.chan6 = AnalogIn(mcp, MCP.P6)
        self.chan7 = AnalogIn(mcp, MCP.P7)
        self.channels = [self.chan0, self.chan1, self.chan2, self.chan3, self.chan4, self.chan5, self.chan6, self.chan7]

    def get_all_values(self):
        all_values = []
        for c in self.channels:
            value = c.value
            all_values.append(value)
        return all_values

    def get_value(self, channel):
        c = self.channels[channel]
        return c.value

    def get_voltage(self, channel):
        c = self.channels[channel]
        return c.voltage

    def analog_lick(self):
        return self.get_value(Settings.analog_lick_channel)

    def e_tape(self):
        return self.get_value(Settings.e_tape_channel)
