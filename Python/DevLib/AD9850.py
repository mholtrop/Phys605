#!/usr/bin/env python3
# Library to run an eBay AD9850 frequency synthesizer on the RPi GPIO
#
# Author: Maurik Holtrop
#
# From the datasheet:
# A serial load is initiated by pulsing the W_clk high, low, followed by
# pulsing the FQ_UD high,low.
# After this sequence 40 bits are clocked in, LSB first, with data load on the clock rise.
# After the 40 bits are send, they are loaded into the device by a pulse on FQ_UD high, low.
#
# A clock pulse has a minimum high time of 3.5 ns, and minimum low time of 3.5 ns.
# The FQ_UD has 7 ns and 7 ns. The minimum RESET width is 13 times CLKIN, so 13*8ns = 104ns
# for the typical module with a 125 MHz oscillator.
#
# Serial data load:
# Frequency bit 0 LSB - Frequency bit 31 MSB  = 32 bits.
# Control bit 0,1 must both be 0              =  2 bits.
# PowerDown bit,                              =  1 bit
# Phase bit 0 - bit 4                         =  5 bits.
#                                              +40 bits
#
# The phase bits shift the output by 11.25 degrees time the value.
#
import time
try:
    import RPi.GPIO as GPIO
except ImportError:
    pass

try:
    import Adafruit_BBIO as GPIO
except ImportError:
    pass


class AD9850:
    """Library for controlling an AD9850 frequency synthesizer."""
    def __init__(self, reset_pin, data_pin, fq_ud_pin, w_clk_pin):
        """Initialize the code to communicate with the AD9850/1 module.
        The module assumes the pins are specified in the BCM numbering scheme."""

        GPIO.setmode(GPIO.BCM)
        self._RESET = reset_pin
        self._DATA = data_pin
        self._FQ_UD = fq_ud_pin
        self._W_CLK = w_clk_pin

        self.phase = 0
        self.freq = 0
        self._powerdown = 0

        GPIO.setup(self._W_CLK, GPIO.OUT)
        GPIO.setup(self._FQ_UD, GPIO.OUT)
        GPIO.setup(self._DATA, GPIO.OUT)
        GPIO.setup(self._RESET, GPIO.OUT)

        GPIO.output(self._W_CLK, 0)  # Set all outputs to zero.
        GPIO.output(self._FQ_UD, 0)
        GPIO.output(self._DATA, 0)
        GPIO.output(self._RESET, 0)

        self.reset()

    def __del__(self):
        """ Cleanup the GPIO before being destroyed """
        GPIO.cleanup(self._W_CLK)
        GPIO.cleanup(self._FQ_UD)
        GPIO.cleanup(self._DATA)
        GPIO.cleanup(self._RESET)

    def reset(self):
        GPIO.output(self._RESET, 1)  # Reset the chip.
        time.sleep(0.0002)           # Sleep 0.2 ms = 200 ns
        GPIO.output(self._RESET, 0)

    def set_frequency(self, frequency, phase=None):
        """ Send a new frequency to the device. This assumes it is running
        with a 125 MHz crystal. """
        self.freq = int(frequency*(2**32)/125000000)  # Normalize to crystal frequency
        if phase is not None:
            self.phase = phase
        self.send_data()

    def get_frequency(self):
        """ Return the current frequency setting. (not read from device)"""
        return self.freq * 125000000 / (2 ** 32)

    def send_data(self):
        """This actually sends the bits to the device."""

        # Send serial initialization sequence
        GPIO.output(self._W_CLK, 1)
        GPIO.output(self._W_CLK, 0)
        GPIO.output(self._FQ_UD, 1)
        GPIO.output(self._FQ_UD, 0)
        # Send out the 40 bits
        self.send_bits(self.freq, 32)
        self.send_bits(0, 2)
        self.send_bits(self._powerdown, 1)
        self.send_bits(self.phase, 5)
        GPIO.output(self._FQ_UD, 1)
        # Load the data
        GPIO.output(self._FQ_UD, 0)

    def send_bits(self, data, nbits):
        """Send a sequence of nbits bits from data to output, LSB first."""

        for i in range(nbits):
            GPIO.output(self._W_CLK, 0)  # Make sure clock is low.
            bit = (data & 0b01)
            data >>= 1
            GPIO.output(self._DATA, bit)
            GPIO.output(self._W_CLK, 1)  # load the bit.
        GPIO.output(self._DATA, 0)
        GPIO.output(self._W_CLK, 0)


def main(argv):
    """Test code for the AD9850 driver.
        If no arguments supplied, assume RESET:22,DATA:23,FQ_UD:24,W_CLK:25"""

    if len(argv) > 1:
        assert len(argv) == 5
        reset = int(argv[1])
        data = int(argv[2])
        fq_ud = int(argv[3])
        w_clk = int(argv[4])
    else:
        reset = 22
        data = 23
        fq_ud = 24
        w_clk = 25              			# Define GPIO pins

    ad = AD9850(reset, data, fq_ud, w_clk)

    try:
        fr = 10
        while True:
            ad.set_frequency(fr)
            fr += 4
            if fr > 10000000:
                fr = 10
            time.sleep(0.01)

    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == '__main__':
    import sys
    import time

    main(sys.argv)
