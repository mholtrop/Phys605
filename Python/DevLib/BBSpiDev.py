# BBSpiDev = Bit Bang SPI device.
#
# This is a software, pure Python, based SPI interface that uses regular GPIO lines.
# It is a heavily modified version of the Adafruit_GPIO/SPI.py example. The reasons
# for modifying are plenty, but mainly to make this Python class a drop-in replacement
# for the _standard_ spidev implementation, rather than needing to go fully the Adafruit way
# of dealing with SPI.
#
#
# This original Adafruit_GPIO/SPI.py is found here:
# https://raw.githubusercontent.com/adafruit/Adafruit_Python_GPIO/master/Adafruit_GPIO/SPI.py
#
##### Copyright notice on the original example:
#
# Copyright (c) 2014 Adafruit Industries
# Author: Tony DiCola
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
try:
    import RPi.GPIO as GPIO             # Import the Raspberry Pi version of GPIO
except:
    try:
        import Adafruit_BBIO as GPIO    # If you are using a Beagle Bone.
    except:
        raise RuntimeError("It seems that no GPIO system was found. Please check your installation.")

import operator

class BBSpiDev(object):
    """Software-based implementation of the SPI protocol over GPIO pins."""

    def __init__(self, CS,CLK,MOSI=None,MISO=None):
        """Initialize bit bang (or software) based SPI.
        If MOSI or MISO are set to None then writes (reads) will be disabled and fail
        with an error. Otherwise:
        CS  -> the chip select pin.
        CLK -> the clock pin.
        MOSI-> the Master Out/Slave in,  or chip data in pin.
        MISO-> the Master In /Slave out, or chip data out pin.
        """
        self._sclk = CLK
        self._mosi = MOSI
        self._miso = MISO
        self._cs = CS

        # Set pins as outputs/inputs.
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self._sclk, GPIO.OUT)
        if self._mosi is not None:
            GPIO.setup(self._mosi, GPIO.OUT)
        if self._miso is not None:
            GPIO.setup(self._miso, GPIO.IN)
        if self._cs is not None:
            GPIO.setup(self._cs, GPIO.OUT)
            # Assert SS high to start with device communication off.
            GPIO.output(self._cs,1)

        # Assume mode 0.
        self.mode=0
        self.lsbfirst=True

    def __del__(self):
        """Cleanup the GPIO when closing. """
        GPIO.cleanup(self._sclk)
        if self._mosi is not None:
            GPIO.cleanup(self._mosi)
        if self._miso is not None:
            GPIO.cleanup(self._miso)
        if self._cs is not None:
            GPIO.cleanup(self._cs)

    def close(self):
        """There is nothing to close """
        pass

    @property
    def mode(self):
        return(self.__mode)

    @mode.setter
    def mode(self, mode):
        """Set SPI mode which controls clock polarity and phase.  Should be a
        numeric value 0, 1, 2, or 3.  See wikipedia page for details on meaning:
        http://en.wikipedia.org/wiki/Serial_Peripheral_Interface_Bus
        """
        self.__mode=mode
        if mode < 0 or mode > 3:
            raise ValueError('Mode must be a value 0, 1, 2, or 3.')
        if mode & 0x02:
            # Clock is normally high in mode 2 and 3.
            self._clock_base = GPIO.HIGH
        else:
            # Clock is normally low in mode 0 and 1.
            self._clock_base = GPIO.LOW
        if mode & 0x01:
            # Read on trailing edge in mode 1 and 3.
            self._read_leading = False
        else:
            # Read on leading edge in mode 0 and 2.
            self._read_leading = True
        # Put clock into its base state.
        GPIO.output(self._sclk, self._clock_base)

    @property
    def lsbfirst(self):
        return(self.__lsbfirst)


    @lsbfirst.setter
    def lsbfirst(self, order):
        """Set order of bits to be read/written over serial lines.
        If set to False, we read/write most-significant first,
        If set to True, we read/write  least-signifcant first (default).
        """
        # Set self._mask to the bitmask which points at the appropriate bit to
        # read or write, and appropriate left/right shift operator function for
        # reading/writing.
        self.__lsbfirst = order
        if order == False:
            self._mask = 0x01
            self._write_shift = operator.rshift
            self._read_shift = operator.lshift
        else:
            self._mask = 0x80
            self._write_shift = operator.lshift
            self._read_shift = operator.rshift

    @property
    def max_speed_hz(self):
        return(0)

    @max_speed_hz.setter
    def max_speed_hz(self,val):
        """max_speed_hz is not implemented """
        print("max_speed_hz is ignored for software SPI")


    def writebytes(self, data, assert_ss=True, deassert_ss=True):
        """Half-duplex SPI write.  If assert_ss is True, the SS line will be
        asserted low, the specified bytes will be clocked out the MOSI line, and
        if deassert_ss is True the SS line be put back high.
        """
        # Fail MOSI is not specified.
        if self._mosi is None:
            raise RuntimeError('Write attempted with no MOSI pin specified.')
        if assert_ss and self._cs is not None:
            GPIO.output(self._cs,0)
        for byte in data:
            for i in range(8):
                # Write bit to MOSI.
                if self._write_shift(byte, i) & self._mask:
                    GPIO.output(self._mosi,1)
                else:
                    GPIO.output(self._mosi,0)
                # Flip clock off base.
                GPIO.output(self._sclk, not self._clock_base)
                # Return clock to base.
                GPIO.output(self._sclk, self._clock_base)
        if deassert_ss and self._cs is not None:
            GPIO.output(self._cs,1)

    def readbytes(self, length, assert_ss=True, deassert_ss=True):
        """Half-duplex SPI read.  If assert_ss is true, the SS line will be
        asserted low, the specified length of bytes will be clocked in the MISO
        line, and if deassert_ss is true the SS line will be put back high.
        Bytes which are read will be returned as a bytearray object.
        """
        if self._miso is None:
            raise RuntimeError('Read attempted with no MISO pin specified.')
        if assert_ss and self._cs is not None:
            GPIO.output(self._cs,0)
        result = bytearray(length)
        for i in range(length):
            for j in range(8):
                # Flip clock off base.
                GPIO.output(self._sclk, not self._clock_base)
                # Handle read on leading edge of clock.
                if self._read_leading:
                    if GPIO.input(self._miso):
                        # Set bit to 1 at appropriate location.
                        result[i] |= self._read_shift(self._mask, j)
                    else:
                        # Set bit to 0 at appropriate location.
                        result[i] &= ~self._read_shift(self._mask, j)
                # Return clock to base.
                GPIO.output(self._sclk, self._clock_base)
                # Handle read on trailing edge of clock.
                if not self._read_leading:
                    if GPIO.input(self._miso):
                        # Set bit to 1 at appropriate location.
                        result[i] |= self._read_shift(self._mask, j)
                    else:
                        # Set bit to 0 at appropriate location.
                        result[i] &= ~self._read_shift(self._mask, j)
        if deassert_ss and self._cs is not None:
            GPIO.output(self._cs,1)
        return result

    def xfer(self,data):
        """Simulate the xfer (transfer data) function of spidev.
       Bytes of data are transferred and between each byte the CS line is
       deasserted and reasserted (0->1 1->0) to indicate next byte.
       """
        return(self.transer(data,xfer_mode=1))

    def xfer2(self,data):
        """Simulate the xfer2 (transfer data without cs toggle) function of spidev.
       Bytes of data are transferred as one continuous bitstream.
       """
        return(self.transer(data,xfer_mode=2))

    def transfer(self, data, assert_ss=True, deassert_ss=True, xfer_mode=1):
        """Full-duplex SPI read and write.  If assert_ss is true, the SS line
        will be asserted low, the specified bytes will be clocked out the MOSI
        line while bytes will also be read from the MISO line, and if
        deassert_ss is true the SS line will be put back high.  Bytes which are
        read will be returned as a bytearray object.
        """
        if self._mosi is None:
            raise RuntimeError('Write attempted with no MOSI pin specified.')
        if self._mosi is None:
            raise RuntimeError('Read attempted with no MISO pin specified.')
        if self._cs is None or (xfer_mode == 1 and ( not deassert_ss or not assert_ss)):
            raise RuntimeError('xfer_mode=1 must lower and raise the CS pin.')

        if assert_ss and self._cs is not None:
            GPIO.output(self._cs,0)
        result = bytearray(len(data))
        for i in range(len(data)):
            for j in range(8):
                # Write bit to MOSI.
                if self._write_shift(data[i], j) & self._mask:
                    GPIO.output(self._mosi,1)
                else:
                    GPIO.output(self._mosi,0)
                # Flip clock off base.
                GPIO.output(self._sclk, not self._clock_base)
                # Handle read on leading edge of clock.
                if self._read_leading:
                    if GPIO.input(self._miso):
                        # Set bit to 1 at appropriate location.
                        result[i] |= self._read_shift(self._mask, j)
                    else:
                        # Set bit to 0 at appropriate location.
                        result[i] &= ~self._read_shift(self._mask, j)
                # Return clock to base.
                GPIO.output(self._sclk, self._clock_base)
                # Handle read on trailing edge of clock.
                if not self._read_leading:
                    if GPIO.input(self._miso):
                        # Set bit to 1 at appropriate location.
                        result[i] |= self._read_shift(self._mask, j)
                    else:
                        # Set bit to 0 at appropriate location.
                        result[i] &= ~self._read_shift(self._mask, j)

            if xfer_mode==1 and self._cs is not None:
                GPIO.output(self._ss,1)
                GPIO.output(self._ss,0)

        if deassert_ss and self._cs is not None:
            GPIO.output(self._ss,1)
        return result
