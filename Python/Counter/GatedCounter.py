#!/usr/bin/env python

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
    i=0
    while i < 1000:
        GPIO.output(Counter_Clear,1) # Clear the counter.
        GPIO.output(Counter_Clear,0) # Counter ready to count.
        GPIO.output(Counter_Gate,1)  # Start the counter
        x = 0                        # Do something we want to time.
        for j in range(1000):
            x=x+j
        i += 1
        GPIO.output(Counter_Gate,0) # Stop the counter.
        count = LoadAndShift(24)
        print "{:04d}, {:6d}".format(i,count)
        sys.stdout.flush()
        time.sleep(0.01)

    Cleanup()


if __name__ == "__main__":
    Main()
    sys.exit()
