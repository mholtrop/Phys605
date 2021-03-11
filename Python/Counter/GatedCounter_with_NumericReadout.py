#!/usr/bin/env python

try:
    import RPi.GPIO as GPIO
except ImportError:
    pass

import time
import sys


OUT_CLK = 23
OUT_DATA = 24
OUT_CS_bar = 25

Counter_Clear = 17
Counter_Gate = 16


Serial_In = 18   # GPIO pin for the SER pin of the shifter
Serial_CLK = 19   # GPIO pin for the CLK pin of the shifter
Serial_Load = 20   # GPIO pin for the SH/LD-bar pin of the shifter
Serial_N = 24   # Number of bits to shift in. 8 bits for every SN74HC165


def setup():
    """Set the RPi to read the shifters and communicate with the MAX7219 """
    GPIO.setmode(GPIO.BCM)  # Set the numbering scheme to correspond to numbers on Pi Wedge.

    GPIO.setup(Serial_CLK, GPIO.OUT)
    GPIO.setup(Serial_In, GPIO.IN)
    GPIO.setup(Serial_Load, GPIO.OUT)
    GPIO.output(Serial_CLK, 0)
    GPIO.output(Serial_Load, 1)

    GPIO.setup(Counter_Clear, GPIO.OUT)
    GPIO.setup(Counter_Gate, GPIO.OUT)
    GPIO.output(Counter_Clear, 1)
    GPIO.output(Counter_Clear, 0)
    GPIO.output(Counter_Gate, 0)

    # Initialize the MAX7219 output display
    GPIO.setup(OUT_CLK, GPIO.OUT)
    GPIO.setup(OUT_DATA, GPIO.OUT)
    GPIO.setup(OUT_CS_bar, GPIO.OUT)
    GPIO.output(OUT_CLK, 0)
    GPIO.output(OUT_DATA, 0)
    GPIO.output(OUT_CS_bar, 1)


def init(mode):
    """ Initialize the MAX7219 Chip. Mode=1 is for numbers, mode=2 is no-decode"""
    write_char(0x0F, 0x01)  # Test ON
    time.sleep(0.5)
    write_char(0x0F, 0x00)  # Test OFF

    write_char(0x0B, 0x07)  # All 8 digits
    write_char(0x0A, 0x0B)  # Quite bright
    write_char(0x0C, 1)     # Set for normal operation.
    if mode == 1:
        write_char(0x09, 0xFF)  # Decode mode
    else:
        write_char(0x09, 0x00)  # Raw mode


def write_data(data):
    """Write the 16 bit data to the output """
    GPIO.output(OUT_CS_bar, 0)

    for i in range(16):  # send out 16 bits.
        GPIO.output(OUT_CLK, 0)
        #time.sleep(0.00001)
        bit = data & 0x8000
        GPIO.output(OUT_DATA, bit)
        #time.sleep(0.00001)
        GPIO.output(OUT_CLK, 1)
        #time.sleep(0.00001)
        data <<= 1
        if i == 7:
            GPIO.output(OUT_CLK, 0)
            GPIO.output(OUT_DATA, 0)
        #    time.sleep(0.00003)

    GPIO.output(OUT_DATA, 0)
    GPIO.output(OUT_CLK, 0)
    GPIO.output(OUT_CS_bar, 1)


def write_char(loc, dat):
    """Write dat to loc. If the mode is 1 then dat is a number and loc is the location.
       If mode is 2 then dat is an 8 bit LED position."""
    out = (loc << 8)
    out += dat
    #out += 0b0000000000000000  # Dummy bits
    write_data(out)


def cleanup():
    write_char(0x0C, 0x0)  # Turn off
    GPIO.cleanup()


def write_int(n):
    """ Write the integer n on the display """
    if n > 99999999:
        for i in range(8):
            write_char(i + 1, 0x0A)
        return

    for i in range(8):
        n, d = divmod(n, 10)
        if n == 0 and d == 0:
            write_char(i + 1, 0x0F)  # Blank
        else:
            write_char(i + 1, d)


def load_and_shift(nbits=24):
    """ Load a number into the N shifters and then read it out by shifting."""
    GPIO.output(Serial_Load, 0)  # load data
    GPIO.output(Serial_Load, 1)  # Ready to shift in.

    out = 0
    for i in range(nbits):
        bit = GPIO.input(Serial_In)    # First bit is already present on SER after load.
        out <<= 1                      # Shift the out bits one to the left.
        out += bit                     # Add the bit we just read.
        GPIO.output(Serial_CLK, GPIO.HIGH)  # Clock High loads next bit
        GPIO.output(Serial_CLK, GPIO.LOW)   # Clock Low resets cycle.
    return out


def main():
    """ Run a basic counter code. """
    print("send on")
    setup()
    init(1)
    print("counting")
    i = 0
    while i < 1000:
        GPIO.output(Counter_Clear, 1)  # Clear the counter.
        GPIO.output(Counter_Clear, 0)  # Counter ready to count.
        GPIO.output(Counter_Gate, 1)   # Start the counter
        x = 0                          # Do something we want to time.
        for j in range(1000):
            x = x + j
        i += 1
        GPIO.output(Counter_Gate, 0)  # Stop the counter.
        sys.stdout.flush()
        count = load_and_shift(24)
        write_int(count)
        print("{:04d}, {:6d}".format(i, count))
        sys.stdout.flush()
        time.sleep(0.01)

    cleanup()


if __name__ == "__main__":
    main()
    sys.exit()
