#!/usr/bin/env python
# The line above allows this script to be run as an executable, so you can run it from the commandline with
# "./ReadSerial1.py"
# instead of
# "python ReadSerial1.py"
# To do so you have to also excute "chmod +x ReadSerial1.py" once to mark
# the script as executable.
#
####################################################################
#  ReadSerial1
####################################################################
#
# This is an example Python script to manipulate some GPIO pins on the
# Raspberry Pi to read out a serial shift register, or PISO register,
# (Parallel-In Serial-Out).
# The code implements a single ended "Bit-Bang" SPI interface.
# SPI = serial peripheral interface: see https://en.wikipedia.org/wiki/Serial_Peripheral_Interface_Bus
# Single ended, since we read data but do not send any.
# "Bit-Bang" because we do not use the hardware interface, but instead use standard GPIO
# ports which we toggle and read.
# For simplicity, and since we are not using multiple SPI devices in this example, we
# do not have a "Chip-Select-bar" (SSbar) signal.
#####################################################################

import RPi.GPIO as GPIO  # Setup the GPIO for RPi
import time
GPIO.setmode(GPIO.BCM)  # Set the numbering scheme to correspond to numbers on Pi Wedge.

Serial_In  = 18   # = MISO  - GPIO pin for the SER (serial out) pin of the shifter
Serial_CLK = 19   # = CLK   - GPIO pin for the CLK (clock) pin of the shifter
Serial_Load= 20   # =       - GPIO pin the SH/LD-bar pin of the shifter.
Serial_N   = 24   # Number of bits to shift in. 8 bits for every SN74HC165
# If you connect 2 or more SN74HC165 chips together, you need to increment Serial_N
# accordingly. Also, if you are not filling all the bits of the SN74HC165.
#
# Setup the GPIO Pins
#
GPIO.setup(Serial_In,   GPIO.IN)
GPIO.setup(Serial_CLK,  GPIO.OUT)
GPIO.setup(Serial_Load, GPIO.OUT)
GPIO.output(Serial_Load,GPIO.HIGH)  # Load is High = ready to shift. Low = load data.
GPIO.output(Serial_CLK, GPIO.LOW)
#
# Define Python functions to do the work for us.
#
def Load_Shifter():
    ''' Load the 8-bit parallel data into the shifter by toggling Serial_Load low '''
    GPIO.output(Serial_Load,GPIO.LOW)
    GPIO.output(Serial_Load,GPIO.HIGH)


def Read_Data(shift_n):
    ''' Shift the data into the shifter and return the obtained value.
        The bits are expected to come as Most Significant Bit (MSB) First
        to Least Significant Bit (LSB).
        Input: shift_n - Number of bits to shift in.
        Output:   out  - The data shifted in.'''

    # The SN74HC165 chip will immediately set the SER output pin equal
    # to the H input pin upon a load. So we need to read the pin first.
    # Then on a clock low->high transition, the shift register shifts the
    # data, and the bit on the G input pin is shifted to SER, etc.
    out=0
    for i in range(shift_n):           # Run the loop shift_n times.
        bit = GPIO.input(Serial_In)    # First bit is already present on SER after load.
        out <<= 1                      # Shift the bits in "out" one position to the left.
        out += bit                     # Add the bit we just read in the LSB location of out.
        GPIO.output(Serial_CLK, GPIO.HIGH) # Clock High loads next bit into SER of chip.
        GPIO.output(Serial_CLK, GPIO.LOW)  # Clock back to low.

    return(out)                        # Return the data.

def Main():
    ''' Example main function. This will read ONE value from the shifter and print it.'''
    #
    # Clearly, you would need to change this part to suit your needs.
    #
    Load_Shifter()              # Load data into the shifters.
    val = Read_Data(Serial_N)   # Read the data from the shifters.

    # Print the value is decimal, hexadecimal, and binary format.
    # Binary format: {:0b} prints the value in 1 and 0,
    if Serial_N < 9:
        print "Value: {:3d} (0x{:02X} = 0b{:08b})".format( val,val,val)
    else:
        # For large numbers, use the second line, since a 24 bit word becomes really hard to read.
        # To make it easier, we print the highest 8 bits (val>>16), the next 8 bits (val>>8)&0xFF,
        # and the last 8 bits (val&0xFF) in groups.
        # Here >> is the shift right operator, and & is the logical AND operator.
        print "Value: {:7d} (0x{:06X} = 0b{:08b} {:08b} {:08b})".format( val,val,(val>>16)&0xFF,(val>>8)&0xFF,val&0xFF)

    GPIO.cleanup()

# This following bit of code allows you to load this script into Python at the commandline
# or as part of another script, and in those cases NOT execute the Main() function.
# If you execute the script from the command prompt, then the name of the scrtipt will
# be set to __main__, so then execute the Main() function.
if __name__ == "__main__":
    Main()
