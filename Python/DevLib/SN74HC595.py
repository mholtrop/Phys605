#!/usr/bin/env python
####################################################################
#  SN74HC595
#  Author: Maurik Holtrop
####################################################################
#
# This is a simple Python module to write to serial shift register SN74HC595.
# Such registers can be used as a port expander for output, where the SN74HC165 can be used as a
# port expander for input.
# The SN74HC595 is a PISO register (Parallel-In Serial-Out).
# The code implements a single ended "Bit-Bang" SPI interface.
# SPI = serial peripheral interface: see https://en.wikipedia.org/wiki/Serial_Peripheral_Interface_Bus
# Single ended, since we read data but do not send any.
# "Bit-Bang" because we do not use the hardware interface, but instead use standard GPIO
# ports which we toggle and read.
# Note that you cannot use the hardware SPI interface without adding
# a tri-state buffer to your circuit.
# For simplicity, and since we are not using multiple SPI devices in this example, we
# do not have a "Chip-Select-bar" (SSbar) signal.
#####################################################################

try:
    import RPi.GPIO as GPIO
except:
    pass
try:
    import Adafruit_BBIO as GPIO
except:
    pass
import time
import sys


class SN74HC595:

    def __init__(self, serial_out, serial_clk, serial_load, serial_clear, serial_n=8):
        """Initialize the module.
        Input:
         * serial_out = SER = GPIO pin for the output data bit, connect to the SER (14) output of the chip.
         * serial_clk = SRCLK = GPIO pin for the clock, connect to SRCLK (11) of the chip.
         * serial_load= RCLK = GPIO pin for the set-ouput, connect to RCLK (12) of the chip.
         * serial_clear = SRCLR-bar = GPIO pin for the clear, connect to SRCLR-bar (10) of the chip.
         * serial_n   = number of bits to read, default=8
         """
        GPIO.setmode(GPIO.BCM)  # Set the numbering scheme to correspond to numbers on Pi Wedge.
        self.Serial_Out = serial_out  # = MOSI
        self.Serial_CLK = serial_clk  # = CLK
        self.Serial_Load = serial_load  # = Load
        self.Serial_Clear = serial_clear  # = Clear
        self.Serial_N = serial_n   # Number of bits to shift in. 8 bits for every SN74HC165.
        #
        # Setup the GPIO Pins
        #
        GPIO.setup(self.Serial_Out, GPIO.OUT)
        GPIO.setup(self.Serial_CLK, GPIO.OUT)
        GPIO.setup(self.Serial_Load, GPIO.OUT)
        if self.Serial_Clear is not None:
            GPIO.setup(self.Serial_Clear, GPIO.OUT)
            GPIO.output(self.Serial_Clear, GPIO.HIGH)  # Load is High = ready to shift. Low = load data.
        GPIO.output(self.Serial_CLK, GPIO.LOW)

    def __del__(self):          # This is automatically called when the class is deleted.
        """Delete and cleanup."""
        GPIO.cleanup(self.Serial_Out)
        GPIO.cleanup(self.Serial_CLK)
        GPIO.cleanup(self.Serial_Load)
        if self.Serial_Clear is not None:
            GPIO.cleanup(self.Serial_Clear)

    def clear(self):
        """Clear the register."""
        GPIO.output(self.Serial_Clear, GPIO.LOW)
        GPIO.output(self.Serial_Clear, GPIO.HIGH)
        self.set_output()

    def set_output(self):
        """Load the parallel data into the shifter by toggling Serial_Load low."""
        GPIO.output(self.Serial_Load, GPIO.HIGH)
        GPIO.output(self.Serial_Load, GPIO.LOW)

    def send_data(self, bits_out):
        """ Shift the data from bits_out into the shifter.
        The bits are sent Most Significant Bit (MSB) First
        to Least Significant Bit (LSB) last.
        """
        for i in range(self.Serial_N):        # Run the loop shift_n times.
            bit = (bits_out >> (self.Serial_N - i - 1)) & 1
            GPIO.output(self.Serial_Out, bit)      # First bit is already present on Q after load.
            GPIO.output(self.Serial_CLK, GPIO.HIGH)  # Clock High loads next bit into Q of chip.
            GPIO.output(self.Serial_CLK, GPIO.LOW)   # Clock back to low, rest state.


def main(argv):
    """Test the functioning of the module by sending numbers to the serial chip.
    The code will use:
    Serial_out  = 18
    Serial_CLK = 19
    Serial_Load= 20
    Serial_clear = 21
    """
    sh_out = SN74HC595(18, 19, 20, 21, 8)
    for i in range(256):
        print(f"Now sending {i:3d}")
        sh_out.send_data(i)
        sh_out.set_output()
        time.sleep(1)


if __name__ == '__main__':
    main(sys.argv)
