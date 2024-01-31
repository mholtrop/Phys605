#!/usr/bin/env python3
####################################################################
#  CharLCD
#  Author: Maurik Holtrop
####################################################################
#
# This is a simple driver to use the LCD Character 20x4 (or 16x2 or ...) displays
# based on the HD44780 chip, that use the PCF8574 I2C port expander.
# The code is intended for Python on a Raspberry Pi
#
####################################################################
#
# Documentation:
# LCD Display: https://en.wikipedia.org/wiki/Hitachi_HD44780_LCD_controller
# HD44780 Data sheet: https://www.sparkfun.com/datasheets/LCD/HD44780.pdf
# Character Set - See: https://mil.ufl.edu/4744/docs/lcdmanual/characterset.html
#
# PCF8574 Data sheet: https://www.ti.com/lit/ds/symlink/pcf8574.pdf
# Connection Schematic: https://alselectro.files.wordpress.com/2016/05/image-2.png
#
# Connections:
# PCF8574         HD44780
# P0         ->   RS
# P1         ->   R/W
# P2         ->   EN
# P3         ->   Backlight LED Transistor to LED+
# P4         ->   D4
# P5         ->   D5
# P6         ->   D6
# P7         ->   D7
#
# Data is written to the HD44780 in two 4-bit nibbles.
#
# Acknowledgements:
# -----------------
# This is an adaptation of code found at the
# Circuit Basics site: https://www.circuitbasics.com/raspberry-pi-i2c-lcd-set-up-and-programming/
# Original code found at: https://gist.github.com/DenisFromHR/cc863375a6e19dce359d
# # Modified Python I2C library for Raspberry Pi
# # as found on http://www.recantha.co.uk/blog/?p=4849
# # Joined existing 'i2c_lib.py' and 'lcddriver.py' into a single library
# # added bits and pieces from various sources
# # By DenisFromHR (Denis Pleic)
# # 2015-02-10, ver 0.1
#

try:
    import smbus
except ImportError:
    print("NO SMBUS class found. You must not be on the Raspberry Pi!")

from time import sleep


class CharLCD:
    # commands
    CLEARDISPLAY = 0x01
    RETURNHOME = 0x02
    ENTRYMODESET = 0x04
    DISPLAYCONTROL = 0x08
    CURSORSHIFT = 0x10
    FUNCTIONSET = 0x20
    SETCGRAMADDR = 0x40
    SETDDRAMADDR = 0x80

    # flags for display entry mode
    ENTRYRIGHT = 0x00
    ENTRYLEFT = 0x02
    ENTRYSHIFTINCREMENT = 0x01
    ENTRYSHIFTDECREMENT = 0x00

    # flags for display on/off control
    DISPLAYON = 0x04
    DISPLAYOFF = 0x00
    CURSORON = 0x02
    CURSOROFF = 0x00
    BLINKON = 0x01
    BLINKOFF = 0x00

    # flags for display/cursor shift
    DISPLAYMOVE = 0x08
    CURSORMOVE = 0x00
    MOVERIGHT = 0x04
    MOVELEFT = 0x00

    # flags for function set
    LCD_8BITMODE = 0x10
    LCD_4BITMODE = 0x00
    LCD_2LINE = 0x08
    LCD_1LINE = 0x00
    LCD_5x10DOTS = 0x04
    LCD_5x8DOTS = 0x00

    # flags for backlight control
    BACKLIGHT = 0x08
    NO_BACKLIGHT = 0x00

    LINE_POSITIONS = [0, 0x40, 0x14, 0x54]

    En = 0b00000100  # Enable bit
    Rw = 0b00000010  # Read/Write bit
    Rs = 0b00000001  # Register select bit

    # initializes objects and lcd
    def __init__(self, address=0x027, port=1):
        self._bus = smbus.SMBus(port)
        self._address = address

        self._write_byte(0x03)
        self._write_byte(0x03)
        self._write_byte(0x03)
        self._write_byte(0x02)

        self._write_byte(self.FUNCTIONSET | self.LCD_2LINE | self.LCD_5x8DOTS | self.LCD_4BITMODE)
        self._write_byte(self.DISPLAYCONTROL | self.DISPLAYON)
        self._write_byte(self.CLEARDISPLAY)
        self._write_byte(self.ENTRYMODESET | self.ENTRYLEFT)
        sleep(0.2)

    # clocks EN to latch command
    def _strobe(self, data):
        self._bus.write_byte(self._address, data | self.En | self.BACKLIGHT)
        sleep(.0005)
        self._bus.write_byte(self._address, ((data & ~self.En) | self.BACKLIGHT))
        sleep(.0001)

    def _write_nibble(self, data):
        self._bus.write_byte(self._address, data | self.BACKLIGHT)
        self._strobe(data)

    # write a command to lcd
    def _write_byte(self, cmd, mode=0):
        self._write_nibble(mode | (cmd & 0xF0))         # Write high 4-bits
        self._write_nibble(mode | ((cmd << 4) & 0xF0))  # Write low 4-bits

    # put string function with optional char positioning
    def print(self, string, line=0, pos=0, wrap=0):
        """Write string to the screen on line=line at position=pos
        If wrap=1 then wrap the line onto the next line if it is too long."""
        if line > 3:
            # ERROR we have only 4 lines to work with.
            pos = 0
            self.clear()
            string = "ERROR: only 4 lines "

        # If we do not want wrap, truncate the string at the end of the screen.
        if not wrap:
            max_char = 20 - pos
            string = string[0:max_char]

        # Output the string until the end of the line, then wrap to the next line and continue.
        while len(string):
            self._write_byte(self.SETDDRAMADDR + self.LINE_POSITIONS[line] + pos)
            max_char = 20 - pos
            for char in string[0:max_char]:
                self._write_byte(ord(char), mode=self.Rs)
            string = string[max_char:]
            pos = 0
            line += 1
            if line > 3:
                line = 0

    # clear entire lcd and set to home
    def clear(self):
        """Clear the entire display and return the write point to home."""
        self._write_byte(self.CLEARDISPLAY)
        self._write_byte(self.RETURNHOME)

    def clear_line(self, line):
        """Only clear a single line (by sending 20 spaces.)"""
        self.print(" "*20, line=line, pos=0)

    # define backlight on/off (lcd.backlight(1); off= lcd.backlight(0)
    def backlight(self, state):  # for state, 1 = on, 0 = off
        if state == 1:
            self._bus.write_byte(self._address, self.BACKLIGHT)
        elif state == 0:
            self._bus.write_byte(self._address, self.NO_BACKLIGHT)

    def shift_display(self, right=0):
        """Shift the entire display left (right) by one character."""
        command = self.CURSORSHIFT + self.DISPLAYMOVE
        if right:
            command += self.MOVERIGHT
        self._write_byte(command)

    # add custom characters (0 - 7)
    def load_custom_chars(self, fontdata):
        self._write_byte(self.SETCGRAMADDR)
        for char in fontdata:
            for line in char:
                self._write_byte(line, mode=self.Rs)


def main(argv):
    """Test function for the CharLCD class."""
    lcd = CharLCD()

    if len(argv) > 1:
        line = 0
        for i in range(1, len(argv)):
            lcd.clear_line(line)
            lcd.print(argv[i], line=line, wrap=1)
            line += 1
            if line > 3:
                line = 0
            sleep(1)
    else:
        offset = 33
        for i in range(3):
            for j in range(4):
                string = ""
                for k in range(20):
                    string += chr(offset+k+j*20+i*20*4)
                lcd.print(string, line=j, pos=0)
            sleep(10)
            lcd.clear()
            sleep(1)


if __name__ == '__main__':
    import sys
    main(sys.argv)
