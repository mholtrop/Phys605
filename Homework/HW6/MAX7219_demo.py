#!/usr/bin/env python
#
# This is a DEMO module for the MAX7219 chip.
#
# The MAX7219 is an LED driver that can steer 8x 7-segment numerical display, or
# an 8x8 Matrix of LEDs.
#
# Author: Maurik Holtrop (2020)
#
import time


class MAX7219:
    def __init__(self, data_pin, clk_pin, cs_bar_pin, mode=1):
        """This class helps with driving a MAX7219 LED module using either regular
        GPIO pins, or SPI hardware interface.
        For SPI hardware, set DATA_pin=0, CS_bar_pin=0 or 1, CLK_pin= bus speed (1000000)
        For GPIO "bit-bang" interface, set DATA_pin = Data in (dat),
        CS_bar = to Chip Select (cs), and CLK_pin= Clock (clk)
        A final argument, mode=1 (default) sets number decoding, while
        mode=0 sets raw mode, see the MAX7219 chip data sheet.
        -------
        This code expects the pin numbers in the BSM standard.
        The Raspberry Pi interfacing is done through the RPi.GPIO module
        or the spi module"""

        self._DATA = data_pin
        self._CS_bar = cs_bar_pin
        self._CLK = clk_pin
        self._Mode = mode
        self._dev = None

        if self._DATA > 0:
            # GPIO.setmode(GPIO.BCM)
            # GPIO.setup(self.CLK,GPIO.OUT)
            # GPIO.setup(self.DATA,GPIO.OUT)
            # GPIO.setup(self.CS_bar,GPIO.OUT)
            #
            # GPIO.output(self.CLK,0)
            # GPIO.output(self.DATA,0)
            # GPIO.output(self.CS_bar,1)
            print("Bit-bang mode: Clk={}, Data={}, CS_bar={}".format(self._CLK, self._DATA, self._CS_bar))
        else:
            if self._CLK < 100:
                self._CLK = 1000000
            # self._dev = SpiDev(0,self.CS_bar)
            # self._dev.mode =0
            # self._dev.max_speed_hz=self.CLK
            # self._dev.bits_per_word = 8
            print("SPI dev mode: speed={}", self._CLK)
        self.init(mode)

    def init(self, mode):
        """ DEMO Display module.
        Initialize the demo MAX7219 Chip.
        mode=1 is for numbers, mode=2 is no-decode.
        This will send an initialization sequence to the chip.
        With an __init__ this method is already called."""
        self.write_loc_char(0x0F, 0x01)  # Test ON
        time.sleep(0.5)
        self.write_loc_char(0x0F, 0x00)  # Test OFF

        self.write_loc_char(0x0B, 0x07)  # All 8 digits
        self.write_loc_char(0x0A, 0x0B)  # Quite bright
        self.write_loc_char(0x0C, 1)     # Set for normal operation.
        if mode == 1:
            self._Mode = 1
            self.write_loc_char(0x09, 0xFF)  # Decode mode
        else:
            self._Mode = 0
            self.write_loc_char(0x09, 0x00)  # Raw mode

        self.clear()

    def __del__(self):          # This is automatically called when the class is deleted.
        """Delete and cleanup."""
        self.write_loc_char(0x0C, 0x0)  # Turn off

    def clear(self):
        """Clear the display to all blanks. (it looks off) """
        for i in range(8):
            if self._Mode == 1:
                self.write_loc_char(i + 1, 0x0F)  # Blank
            else:
                self.write_loc_char(i + 1, 0x00)  # Blank

    def set_brightness(self, b):
        """Set the display brightness to B, where 0<=B<16"""
        b = b & 0x0F
        self.write_loc_char(0x0A, b)  # Set brightness

    def write_data(self, data):
        """Write the 16 bit data to the output using SPI or
         "bit-banged" SPI on the GPIO output line.
        This is a "raw" mode write, used internally in these methods."""
        if self._DATA > 0:
            print("CS_bar->0 B:", end="")
            for i in range(16):  # send out 16 bits of data sequentially.
                bit = int((data & 0x8000) > 0)
                print("{}".format(bit), end="")
                data <<= 1
                if i == 7:
                    print("0", end="")

            print("0", end="")
            print("  CS_bar->1")
        else:
            print("SPI: 0x{:x} 0x{:x}".format((data >> 8) & 0xFF, data & 0xFF))

    def write_loc_char(self, loc, dat):
        """Write dat to loc. If the mode is 1 then dat is a number and loc is the location.
        If mode is 0 then dat is an 8 bit LED position.
        This is used internally to display the numbers/characters."""
        if self._DATA > 0:
            out = (loc << 8)
            out += dat
            self.write_data(out)
        else:
            print("SPI: 0x{:x} 0x{:x}".format((dat >> 8) & 0xFF, dat & 0xFF))

    def write_raw(self, n):
        """Write the list of 8-bit integers to the module in raw mode"""
        if self._Mode != 0:
            raise ValueError()
        if type(n) is int:
            print("please provide an tuple or list")

        for i in range(len(n)):
            self.write_loc_char(i + 1, n[i])

    def write_int(self, n):
        """ Write the integer n on the display, shifted left. If n is larger (smaller) than
        fits, an overflow is indicated by all dash."""

        if self._Mode != 1:
            raise ValueError()

        if n > 99999999 or n < -9999999:  # Display overflow, --------
            for i in range(8):
                self.write_loc_char(i + 1, 0x0A)
            return

        if n < 0:
            negative = True
            n = -n
        else:
            negative = False
        for i in range(8):
            n, d = divmod(n, 10)
            if n == 0 and d == 0:
                if i == 0:
                    self.write_loc_char(i + 1, 0x0)  # 0
                else:
                    if negative:
                        self.write_loc_char(i + 1, 0x0A)
                        negative = False
                    else:
                        self.write_loc_char(i + 1, 0x0F)  # Blank
            else:
                self.write_loc_char(i + 1, d)

    def write_float(self, f, form='{:9.6f}'):
        """Write a floating point number. Trying to use a reasonable format.
        You can specify the format with the form= argument, using the python
        style, to use with form="{:4.2f}" or form="{:8.4e}" """

        if self._Mode != 1:
            raise ValueError()

        s = form.format(f)
        loc = 1
        high_bit = 0
        rev = reversed(s[0:8+s.count('.')+s.count('e')])  # Read the letters reversed, starting at the end.
        for c in rev:       # Get each of the numbers/symbols, starting with the rightmost.
            if c == '.':    # If it is the period, then set bit7 but don't count as a digit.
                high_bit = 1
            else:
                if c.isdigit():  # It is a digit.
                    i = int(c)
                    i += high_bit << 7
                    self.write_loc_char(loc, i)
                    loc += 1
                elif c == ' ':
                    self.write_loc_char(loc, 0x0F)  # Write blank
                    loc += 1
                elif c == '+':
                    self.write_loc_char(loc, 0x0B)  # Write E
                    loc += 1
                elif c == '-':
                    self.write_loc_char(loc, 0x0A)  # Write -
                    loc += 1
                elif c == 'e' or c == 'E':          # Skip the E, E- too long.
                    pass
                else:
                    print("Bad char in string: ", c)
                high_bit = 0
        while loc < 9:                      # Fill the end with blanks
            self.write_loc_char(loc, 0x0F)  # Write blank
            loc += 1

    def __str__(self):
        """Write something comforting to the user :-) """
        if self._DATA > 0:
            print("MAX7219 driver interface. GPIO mode: DATA={} CS_bar={} CLK={}", self._DATA, self._CS_bar, self._CLK)
