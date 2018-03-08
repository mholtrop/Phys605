#!/usr/bin/env python
#
# This is a test code is intended to readout an SN74HC165 chip.
# Author: Maurik Holtrop
#
# Basic operation:
#  1) Setup the GPIO input and output ports.
#  2) Send a counter clear signal on the Counter_Clear pin.
#  3) Open the AND (or NAND) gate to the counter clock. (See notes)
#  4) Wait, or run code to be timed.
#  5) Close the AND gate.
#  6) Send a Load signal to the SN74HC165 chip on Serial_Load.
#  7) Readout the SN74HC165 for Serial_N clocks on Serial_CLK by loading the
#     bits from the Serial_In.
#  8) Print the resulting number to the screen.
#
# Notes:
#     * When using the SN74HC193 chip for counting, you can gate by
#       sending the Counter_Gate signal to the "down" clock, and the Clock
#       to be counted to the "up" clock.
#     * When using the SN74HC4040 chip, add a NAND gate to the CLK input.
#       One input of the NAND gate goes to the Counter_Gate, the another
#       to the clock to be counted.
#
# See also the ReadSerial.py code.
#
import RPi.GPIO as GPIO
import time
import sys

Counter_Clear = 17
Counter_Gate = 16


Serial_In  = 18   # GPIO pin for the SER pin of the shifter
Serial_CLK = 19   # GPIO pin for the CLK pin of the shifter
Serial_Load= 20   # GPIO pin for the SH/LD-bar pin of the shifter
Serial_N   = 8   # Number of bits to shift in. 8 bits for every SN74HC165

def Setup():
    '''Set the RPi to read the shifterers and communucate with the MAX7219 '''
    GPIO.setmode(GPIO.BCM)  # Set the numbering scheme to correspond to numbers on Pi Wedge.

    GPIO.setup(Serial_CLK,GPIO.OUT)
    GPIO.setup(Serial_In,GPIO.IN)
    GPIO.setup(Serial_Load,GPIO.OUT)
    GPIO.output(Serial_CLK,0)
    GPIO.output(Serial_Load,1)

    GPIO.setup(Counter_Clear,GPIO.OUT)
    GPIO.setup(Counter_Gate,GPIO.OUT)
    GPIO.output(Counter_Clear,1)
    GPIO.output(Counter_Clear,0)
    GPIO.output(Counter_Gate,0)


def Cleanup():
    GPIO.cleanup()

def LoadAndShift(Nbits=Serial_N):
    ''' Load a numner into the N shifters and then read it out by shifting.'''
    GPIO.output(Serial_Load,0) # load data
    GPIO.output(Serial_Load,1) # Ready to shift in.

    out=0
    for i in range(Serial_N):
        bit = GPIO.input(Serial_In)    # First bit is already present on SER after load.
        out <<= 1                      # Shift the out bits one to the left.
        out += bit                     # Add the bit we just read.
        GPIO.output(Serial_CLK, 1) # Clock High loads next bit
        GPIO.output(Serial_CLK, 0)  # Clock Low resets cycle.
    return(out)

def Main():
    ''' Run a basic counter code. '''
    Setup()
    print "counting."
    sys.stdout.flush()
    for i in range(100):
        GPIO.output(Counter_Clear,1) # Clear the counter.
        GPIO.output(Counter_Clear,0) # Counter ready to count.
        GPIO.output(Counter_Gate,1)  # Start the counter
        # x = 0                        # Do something we want to time.
        # for j in range(1000):
        #     x=x+j
        time.sleep(1.)               # Sleep for 1 second while the counter counts.
        GPIO.output(Counter_Gate,0) # Stop the counter.
        count = LoadAndShift(24)
        print("{:04d}, {:6d}".format(i,count)) # Print the itteration and the counts.
        sys.stdout.flush()
        time.sleep(1.)              # Wait a sec before starting again.

    Cleanup()


if __name__ == "__main__":
    Main()
    sys.exit()
