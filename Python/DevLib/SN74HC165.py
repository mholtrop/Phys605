#!/usr/bin/env python
####################################################################
#  SN74HC165
#  Author: Maurik Holtrop
####################################################################
#
# This is a simple Python module to read out a serial shift register SN74HC165,
# or PISO register (Parallel-In Serial-Out), using the RPi.
# The code implements a single ended "Bit-Bang" SPI interface.
# SPI = serial peripheral interface: see https://en.wikipedia.org/wiki/Serial_Peripheral_Interface_Bus
# Single ended, since we read data but do not send any.
# "Bit-Bang" because we do not use the hardware interface, but instead use standard GPIO
# ports which we toggle and read. Note that you cannot use the hardware interface without adding
# a tri-state buffer to your circuit.
# For simplicity, and since we are not using multiple SPI devices in this example, we
# do not have a "Chip-Select-bar" (SSbar) signal.
#####################################################################

import RPi.GPIO as GPIO  # Setup the GPIO for RPi
import time
import sys

class SN74HC165:

    def __init__(self,Serial_In,Serial_CLK,Serial_Load,Serial_N=8):
        '''Initialize the module.
        Input:
         * Serial_in  = GPIO pin for the input data bit, connect to the Q output of the chip.
         * Serial_CLK = GPIO pin for the clock, connect to CLK of the chip.
         * Selial_Load= GPIO pin for the load signal (CS_bar like behavior), connect to LOAD of the chip.
         * Serial_N   = number of bits to read, default=8
         '''
        GPIO.setmode(GPIO.BCM)  # Set the numbering scheme to correspond to numbers on Pi Wedge.
        self.Serial_In  = Serial_In  # = MISO - GPIO pin for the Q (serial out) pin of the shifter
        self.Serial_CLK = Serial_CLK # = CLK  - GPIO pin for the CLK (clock) pin of the shifter
        self.Serial_Load= Serial_Load# = Load - GPIO pin the SH/LD-bar pin of the shifter.
        self.Serial_N   = Serial_N   # Number of bits to shift in. 8 bits for every SN74HC165.
        #
        # Setup the GPIO Pins
        #
        GPIO.setup(Serial_In,   GPIO.IN)
        GPIO.setup(Serial_CLK,  GPIO.OUT)
        GPIO.setup(Serial_Load, GPIO.OUT)
        GPIO.output(Serial_Load,GPIO.HIGH)  # Load is High = ready to shift. Low = load data.
        GPIO.output(Serial_CLK, GPIO.LOW)

    def __del__(self):          # This is automatically called when the class is deleted.
        '''Delete and cleanup.'''
        GPIO.cleanup(self.Serial_In)
        GPIO.cleanup(self.Serial_CLK)
        GPIO.cleanup(self.Serial_Load)

    def Load_Shifter(self):
        ''' Load the parallel data into the shifter by toggling Serial_Load low '''
        GPIO.output(self.Serial_Load,GPIO.LOW)
        GPIO.output(self.Serial_Load,GPIO.HIGH)

    def Read_Data(self):
        ''' Shift the data into the shifter and return the obtained value.
        The bits are expected to come as Most Significant Bit (MSB) First
        to Least Significant Bit (LSB) last.
        Output:   out  - The data shifted in returned as integer.'''

        # The SN74HC165 chip will immediately set the SER output pin equal
        # to the H input pin upon a load. So we need to read the pin first.
        # Then on a clock low->high transition, the shift register shifts the
        # data, and the bit on the G input pin is shifted to SER, etc.
        out=0
        for i in range(self.Serial_N):        # Run the loop shift_n times.
            bit = GPIO.input(self.Serial_In)  # First bit is already present on Q after load.
            out <<= 1                         # Shift the bits in "out" one position to the left.
            out += bit                        # Add the bit we just read in the LSB location of out.
            GPIO.output(self.Serial_CLK, GPIO.HIGH) # Clock High loads next bit into Q of chip.
            GPIO.output(self.Serial_CLK, GPIO.LOW)  # Clock back to low, rest state.

        return(out)                        # Return the data.
#
# The code below turns this module into a program as well
# allowing you to run it in test mode from the command line.
#
def main(argv):
    '''Test the functioning of the module by reading N
    numbers from serial.
    The code will use:
    Serial_In  = 18
    Serial_CLK = 19
    Serial_Load= 20
    '''
    S = SN74HC165(18,19,20,8)
    S.Load_Shifter()
    num = S.Read_Data()
    print(num)

if __name__ == '__main__':
    main(sys.argv)
