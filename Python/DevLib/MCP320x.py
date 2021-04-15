#!/usr/bin/env python
#
# MCP320x
#
# Author: Maurik Holtrop
#
# This module interfaces with the MCP300x or MCP320x family of chips. These
# are 10-bit and 12-bit ADCs respectively.  The x number indicates the number
# of multiplexed analog inputs:  2 (MCP3202), 4 (MCP3204) or 8 (MCP3208)
# Communications with this chip are over the SPI protocol.
# See: https://en.wikipedia.org/wiki/Serial_Peripheral_Interface_Bus
#
# The version of the code has two SPI interfaces: the builtin hardware
# SPI interface on the RPI, or a "bit-banged" GPIO version.
#
# Bit-Bang GPIO:
#   We emulate a SPI port in software using the GPIO lines.
#   This is a bit slower than the hardware interface, but it is far more
#   clear what is going on, plus the RPi has only one SPI device.
#   Connections: RPi GPIO to  MCP320x
#              CS_bar_pin = CS/SHDN
#              CLK_pin    = CLK
#              MOSI_pin   = D_in
#              MISO_pin   = D_out
#
# Hardware SPI:
#   This uses the builtin hardware on the RPi. You need to enable this with the
#   raspi-config program first. The data rate can be up to 1MHz.
#   Connections: RPi pins to MCP320x
#              CE0 or CE1 = CS/SHDN  (chip select) set CS_bar = 0 or 1
#              SCK        = CLK      set CLK_pin  = 1000000 (transfer speed)
#              MOSI       = D_in     set MOSI_pin = 0
#              MISO       = D_out    set MISO_pin = 0

# The SPI protocol simulated here is MODE=0, CPHA=0, which has a positive polarity clock,
# (the clock is 0 at rest, active at 1) and a positive phase (0 to 1 transition) for reading
# or writing the data. Thus corresponds to the specifications of the MCP320x chips.
#
# From MCP3208 datasheet:
# Outging data : MCU latches data to A/D converter on rising edges of SCLK
# Incoming data: Data is clocked out of A/D converter on falling edges, so should be read on rising edge.
try:
    import RPi.GPIO as GPIO
except ImportError as error:
    pass
try:
    import Adafruit_BBIO as GPIO
except ImportError as error:
    pass

try:
    import spidev
except ImportError as error:
    pass

from DevLib.MyValues import MyValues


class MCP320x:
    """This is an class that implements an interface to the MCP320x ADC chips.
    Standard is the MCP3208, but is will also work wiht the MCP3202, MCP3204, MCP3002, MCP3004 and MCP3008."""

    def __init__(self, cs_bar_pin, clk_pin=1000000, mosi_pin=0, miso_pin=0, chip='MCP3208',
                 channel_max=None, bit_length=None, single_ended=True):
        """Initialize the code and set the GPIO pins.
        The last argument, ch_max, is 2 for the MCP3202, 4 for the
        MCP3204 or 8 for the MCS3208."""

        self._CLK = clk_pin
        self._MOSI = mosi_pin
        self._MISO = miso_pin
        self._CS_bar = cs_bar_pin

        chip_dictionary = {
                "MCP3202": (2, 12),
                "MCP3204": (4, 12),
                "MCP3208": (8, 12),
                "MCP3002": (2, 10),
                "MCP3004": (4, 10),
                "MCP3008": (8, 10)
        }

        if chip in chip_dictionary:
            self._ChannelMax = chip_dictionary[chip][0]
            self._BitLength = chip_dictionary[chip][1]
        elif chip is None and (channel_max is not None) and (bit_length is not None):
            self._ChannelMax = channel_max
            self._BitLength = bit_length
        else:
            print("Unknown chip: {} - Please re-initialize.")
            self._ChannelMax = 0
            self._BitLength = 0
            return

        self._SingleEnded = single_ended
        self._Vref = 3.3
        self._values = MyValues(self.read_adc, self._ChannelMax)
        self._volts = MyValues(self.read_volts, self._ChannelMax)

        # This is used to speed up the SPIDEV communication. Send out MSB first.
        # control[0] - bit7-3: upper 5 bits 0, because we can only send 8 bit sequences.
        #            - bit2   : Start bit - starts conversion in ADCs
        #            - bit1   : Select single_ended=1 or differential=0
        #            - bit0   : D2 high bit of channel select.
        # control[1] - bit7   : D1 middle bit of channel select.
        #            - bit6   : D0 low bit of channel select.
        #            - bit5-0 : Don't care.
        if self._SingleEnded:
            self._control0 = [0b00000110, 0b00100000, 0]  # Pre-compute part of the control word.
        else:
            self._control0 = [0b00000100, 0b00100000, 0]  # Pre-compute part of the control word.

        if self._MOSI > 0:  # Bing Bang mode
            assert self._MISO != 0 and self._CLK < 32
            if GPIO.getmode() != 11:
                GPIO.setmode(GPIO.BCM)        # Use the BCM numbering scheme

            GPIO.setup(self._CLK, GPIO.OUT)     # Setup the ports for in and output
            GPIO.setup(self._MOSI, GPIO.OUT)
            GPIO.setup(self._MISO, GPIO.IN)
            GPIO.setup(self._CS_bar, GPIO.OUT)

            GPIO.output(self._CLK, 0)           # Set the clock low.
            GPIO.output(self._MOSI, 0)          # Set the Master Out low
            GPIO.output(self._CS_bar, 1)        # Set the CS_bar high

        else:
            self._dev = spidev.SpiDev(0, self._CS_bar)  # Start a SpiDev device
            self._dev.mode = 0                          # Set SPI mode (phase)
            self._dev.max_speed_hz = self._CLK          # Set the data rate
            self._dev.bits_per_word = 8                 # Number of bit per word. ALWAYS 8

    def __del__(self):
        """ Cleanup the GPIO before being destroyed """
        if self._MOSI > 0:
            GPIO.cleanup(self._CS_bar)
            GPIO.cleanup(self._CLK)
            GPIO.cleanup(self._MOSI)
            GPIO.cleanup(self._MISO)

    def get_channel_max(self):
        """Return the maximum number of channels"""
        return self._ChannelMax

    def get_bit_length(self):
        """Return the number of bits that will be read"""
        return self._BitLength

    def get_value_max(self):
        """Return the maximum value possible for an ADC read"""
        return 2 ** self._BitLength - 1

    def send_bit(self, bit):
        """ Send out a single bit, and pulse clock."""
        if self._MOSI == 0:
            return
        #
        # The input is read on the rising edge of the clock.
        #
        GPIO.output(self._MOSI, bit)  # Set the bit.
        GPIO.output(self._CLK, 1)     # Rising edge sends data
        GPIO.output(self._CLK, 0)     # Return clock to zero.

    def read_bit(self):
        """ Read a single bit from the ADC and pulse clock."""
        if self._MOSI == 0:
            return 0
        #
        # The output is going out on the falling edge of the clock,
        # and is to be read on the rising edge of the clock.

        # Clock should be already low, and data should already be set.
        GPIO.output(self._CLK, 1)     # Set the clock high. Ready to read.
        bit = GPIO.input(self._MISO)  # Read the bit.
        GPIO.output(self._CLK, 0)     # Return clock low, next bit will be set.

        return bit

    def read_adc(self, channel):
        """This reads the actual ADC value, after connecting the analog multiplexer to
        the desired channel.
        ADC value is returned at a n-bit integer value, with n=10 or 12 depending on the chip.
        The value can be converted to a voltage with:
           volts = data*Vref/(2**n-1)"""
        if channel < 0 or channel >= self._ChannelMax:
            print("Error - chip does not have channel = {}".format(channel))

        if self._MOSI == 0:
            # SPIdev Code
            # This builds up the control word, which selects the channel
            # and sets single/differential more.
            control = [self._control0[0] + ((channel & 0b100) >> 2), self._control0[1]+((channel & 0b011) << 6), 0]
            dat = self._dev.xfer(control)
            value = (dat[1] << 8)+dat[2]  # Unpack the two 8-bit words to a single integer.
            return value

        else:
            # Bit Bang code.
            # To read out this chip you need to send:
            # 1 - start bit
            # 2 - Single ended (1) or differential (0) mode
            # 3 - Channel select: 1 bit for x=2 or 3 bits for x=4,8
            # 4 - MSB first (1) or LSB first (0)
            #
            # Start of sequence sets CS_bar low, and sends sequence
            #
            GPIO.output(self._CLK, 0)                # Make sure clock starts low.
            GPIO.output(self._MOSI, 0)
            GPIO.output(self._CS_bar, 0)             # Select the chip.
            self.send_bit(1)                        # Start bit = 1
            self.send_bit(self._SingleEnded)   # Select single or differential
            if self._ChannelMax > 2:
                self.send_bit(int((channel & 0b100) > 0))  # Send high bit of channel = DS2
                self.send_bit(int((channel & 0b010) > 0))  # Send mid  bit of channel = DS1
                self.send_bit(int((channel & 0b001) > 0))  # Send low  bit of channel = DS0
            else:
                self.send_bit(channel)

            self.send_bit(0)                       # MSB First (for MCP3x02) or don't care.

            # The clock is currently low, and the dummy bit = 0 is on the output of the ADC
            #
            self.read_bit()  # Read the bit.

            data = 0
            for i in range(self._BitLength):
                # Note you need to shift left first, or else you shift the last bit (bit 0)
                # to the 1 position.
                data <<= 1
                bit = self.read_bit()
                data += bit

            GPIO.output(self._CS_bar, 1)  # Unselect the chip.

            return data

    def read_volts(self, channel):
        """Read the ADC value from channel and convert to volts, assuming that Vref is set correctly. """
        return self._Vref * self.read_adc(channel) / self.get_value_max()

    def fast_read_adc0(self):
        """This reads the actual ADC value of channel 0, with as little overhead as possible.
        Use with SPIDEV ONLY!!!!
        returns: The ADC value as an n-bit integer value, with n=10 or 12 depending on the chip."""

        dat = self._dev.xfer(self._control0)
        value = (dat[1] << 8) + dat[2]
        return value

    @property
    def values(self):
        """ADC values presented as a list."""
        return self._values

    @property
    def volts(self):
        """ADC voltages presented as a list"""
        return self._volts

    @property
    def accuracy(self):
        """The fractional voltage of the least significant bit. """
        return self._Vref / float(self.get_value_max())

    @property
    def vref(self):
        """Reference voltage used by the chip. You need to set this. It defaults to 3.3V"""
        return self._Vref

    @vref.setter
    def vref(self, vr):
        self._Vref = vr


def main(argv):
    """Test code for the MCP320x driver. This assumes you are using a MCP3208
    If no arguments are supplied, then use SPIdev for CE0 and read channel 0"""

    if len(argv) < 3:
        print("Args : ", argv)
        cs_bar = 0
        clk_pin = 1000000
        mosi_pin = 0
        miso_pin = 0
        if len(argv) < 2:
            channel = 0
        else:
            channel = int(argv[1])
            
    elif len(argv) < 6:
        print("Please supply: cs_bar_pin clk_pin mosi_pin miso_pin channel")
        sys.exit(1)

    else:
        cs_bar = int(argv[1])
        clk_pin = int(argv[2])
        mosi_pin = int(argv[3])
        miso_pin = int(argv[4])
        channel = int(argv[5])

    adc_chip = MCP320x(cs_bar, clk_pin, mosi_pin, miso_pin)
    try:
        while True:
            value = adc_chip.read_adc(channel)
            print("{:4d}".format(value))
            time.sleep(0.1)
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == '__main__':
    import sys
    import time
    main(sys.argv)
