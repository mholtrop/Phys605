#!/usr/bin/env python
#
# This is a test code is intended to readout a set of 3 SN74HC165 chips
# connected to two SN74HC4040 counters, for a 24-bit serial readout counter.
# The counter input should be gated using a NAND gate to a GPIO pin.
#
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
#
import RPi.GPIO as GPIO
from DevLib import SN74HC165,MAX7219
import time
import sys

Counter_Clear = 17
Counter_Gate = 16


Serial_In  = 18   # GPIO pin for the SER pin of the shifter
Serial_CLK = 19   # GPIO pin for the CLK pin of the shifter
Serial_Load= 20   # GPIO pin for the SH/LD-bar pin of the shifter
Serial_N   = 24   # Number of bits to shift in. 8 bits for every SN74HC165

Max_data = 0        # Use 0 for SPI connection, otherwise use GPIO pin connected to driving
Max_clock= 1000000  # Use clock frequency for SPI connection, otherwise use GPIO pin connected to CLK
Max_cs_bar = 0      # Use channel (CE0 or CE1) for SPI connection, otherwise use GPIO pin for CS

S = None  # Placeholder, make sure you run Setup() before using.
M = None


def Setup():
    '''Set the RPi to read the shifterers and communucate with the MAX7219 '''
    global S
    global M

    GPIO.setmode(GPIO.BCM)  # Set the numbering scheme to correspond to numbers on Pi Wedge.

    S = SN74HC165(Serial_In,Serial_CLK,Serial_Load,Serial_N) # Initialize serial shifter.
    M = MAX7219(Max_data,Max_clock,Max_cs_bar)               # Initialize the display.

    GPIO.setup(Counter_Clear,GPIO.OUT)
    GPIO.setup(Counter_Gate,GPIO.OUT)
    GPIO.output(Counter_Gate,0)
    ClearCounter()

def ClearCounter():
    '''Clear the counter by pulsing the Counter_Clear pin high'''
    GPIO.output(Counter_Clear,1)
    GPIO.output(Counter_Clear,0)

def Cleanup():
    GPIO.cleanup()

def LoadAndShift():
    ''' Load a number into the shifters and then read it out.'''
    S.Load_Shifter()
    return(S.Read_Data())

def Main():
    ''' Run a basic counter code. '''
    Setup()
    print "counting."
    sys.stdout.flush()
    itt=0
    while True:
        itt+=1
        ClearCounter()
        GPIO.output(Counter_Gate,1)  # Start the counter
        # x = 0                        # Do something we want to time.
        # for j in range(1000):
        #     x=x+j
        time.sleep(0.9989611300233423)              # Sleep for not quite 1 second while the counter counts.
        GPIO.output(Counter_Gate,0) # Stop the counter.
        count = LoadAndShift()
        M.WriteInt(count)
        print("{:04d}, {:6d}".format(i,count)) # Print the itteration and the counts.
        sys.stdout.flush()
        time.sleep(1.)              # Wait a sec before starting again.

    Cleanup()


if __name__ == "__main__":
    Main()
    sys.exit()
