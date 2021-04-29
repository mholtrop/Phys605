# -*- coding: utf-8 -*-
#
# LCD Display: https://en.wikipedia.org/wiki/Hitachi_HD44780_LCD_controller
# HD44780 Data sheet: https://www.sparkfun.com/datasheets/LCD/HD44780.pdf
# Character Set - See: https://mil.ufl.edu/4744/docs/lcdmanual/characterset.html
#
# PCF8574 
#
# This is an adaptation of code found at the
# Circuit Basics site: https://www.circuitbasics.com/raspberry-pi-i2c-lcd-set-up-and-programming/
# Original code found at: https://gist.github.com/DenisFromHR/cc863375a6e19dce359d
# """
# Compiled, mashed and generally mutilated 2014-2015 by Denis Pleic
# Made available under GNU GENERAL PUBLIC LICENSE
#
# # Modified Python I2C library for Raspberry Pi
# # as found on http://www.recantha.co.uk/blog/?p=4849
# # Joined existing 'i2c_lib.py' and 'lcddriver.py' into a single library
# # added bits and pieces from various sources
# # By DenisFromHR (Denis Pleic)
# # 2015-02-10, ver 0.1
#
# """

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

    En = 0b00000100  # Enable bit
    Rw = 0b00000010  # Read/Write bit
    Rs = 0b00000001  # Register select bit

    # initializes objects and lcd
    def __init__(self, address=0x027, port=1):
        self._bus = smbus.SMBus(port)
        self._address = address

        self.lcd_write(0x03)
        self.lcd_write(0x03)
        self.lcd_write(0x03)
        self.lcd_write(0x02)

        self.lcd_write(self.FUNCTIONSET | self.LCD_2LINE | self.LCD_5x8DOTS | self.LCD_4BITMODE)
        self.lcd_write(self.DISPLAYCONTROL | self.DISPLAYON)
        self.lcd_write(self.CLEARDISPLAY)
        self.lcd_write(self.ENTRYMODESET | self.ENTRYLEFT)
        sleep(0.2)

    # clocks EN to latch command
    def lcd_strobe(self, data):
        self._bus.write_byte(self._address, data | self.En | self.BACKLIGHT)
        sleep(.0005)
        self._bus.write_byte(self._address, ((data & ~self.En) | self.BACKLIGHT))
        sleep(.0001)

    def lcd_write_four_bits(self, data):
        self._bus.write_byte(self._address, data | self.BACKLIGHT)
        self.lcd_strobe(data)

    # write a command to lcd
    def lcd_write(self, cmd, mode=0):
        self.lcd_write_four_bits(mode | (cmd & 0xF0))
        self.lcd_write_four_bits(mode | ((cmd << 4) & 0xF0))

    # write a character to lcd (or character rom) 0x09: backlight | RS=DR<
    # works!
    def lcd_write_char(self, charvalue, mode=1):
        self.lcd_write_four_bits(mode | (charvalue & 0xF0))
        self.lcd_write_four_bits(mode | ((charvalue << 4) & 0xF0))

    # put string function with optional char positioning
    def lcd_display_string(self, string, line=1, pos=0):
        pos_new = pos
        if line == 1:
            pos_new = pos
        elif line == 2:
            pos_new = 0x40 + pos
        elif line == 3:
            pos_new = 0x14 + pos
        elif line == 4:
            pos_new = 0x54 + pos

        self.lcd_write(0x80 + pos_new)

        for char in string:
            self.lcd_write(ord(char), self.Rs)

    # clear lcd and set to home
    def lcd_clear(self):
        self.lcd_write(self.CLEARDISPLAY)
        self.lcd_write(self.RETURNHOME)

    # define backlight on/off (lcd.backlight(1); off= lcd.backlight(0)
    def backlight(self, state):  # for state, 1 = on, 0 = off
        if state == 1:
            self._bus.write_byte(self._address, self.BACKLIGHT)
        elif state == 0:
            self._bus.write_byte(self._address, self.NO_BACKLIGHT)

    # add custom characters (0 - 7)
    def lcd_load_custom_chars(self, fontdata):
        self.lcd_write(0x40)
        for char in fontdata:
            for line in char:
                self.lcd_write_char(line)
