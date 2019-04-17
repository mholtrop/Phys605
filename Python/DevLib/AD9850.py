#!/usr/bin/env python
# Library to run an eBay AD9850 on the RPi GPIO
#
# Author: Maurik Holtrop
#
# From the datasheet:
# A serial load is initiated by pulsing the W_clk high, low, followed by
# pulsing the FQ_UD high,low.
# After this sequence 40 bits are clocked in, LSB first, with data load on the clock rise.
# After the 40 bits are send, they are loaded into the device by a pulse on FQ_UD high, low.
#
# A clock pulse has a minimum high time of 3.5 ns, and minimum low time of 3.5 ns.
# The FQ_UD has 7 ns and 7 ns. The minimum RESET width is 13 times CLKIN, so 13*8ns = 104ns
# for the typical module with a 125 MHz oscillator.
#
# Serial data load:
# Frequency bit 0 LSB - Frequency bit 31 MSB  = 32 bits.
# Control bit 0,1 must both be 0              =  2 bits.
# PowerDown bit,                              =  1 bit
# Phase bit 0 - bit 4                         =  5 bits.
#                                              +40 bits
#
# The phase bits shift the output by 11.25 degrees time the value.
#
import RPi.GPIO as GPIO
import time

class AD9850:

    def __init__(self,RESET_pin,DATA_pin,FQ_UD_pin,W_CLK_pin):
        '''Initialize the code to communicate with the AD9850/1 module.
        The module assumes the pins are specified in the BCM numbering scheme.'''

        GPIO.setmode(GPIO.BCM)
        self.RESET = RESET_pin
        self.DATA =  DATA_pin
        self.FQ_UD = FQ_UD_pin
        self.W_CLK = W_CLK_pin

        self.phase=0
        self.freq=0
        self.powerdown=0

        GPIO.setup(self.W_CLK, GPIO.OUT)
        GPIO.setup(self.FQ_UD, GPIO.OUT)
        GPIO.setup(self.DATA,  GPIO.OUT)
        GPIO.setup(self.RESET, GPIO.OUT)

        GPIO.output(self.W_CLK, 0) # Set all outputs to zero.
        GPIO.output(self.FQ_UD, 0)
        GPIO.output(self.DATA,  0)
        GPIO.output(self.RESET, 0)

        self.Reset()

    def __del__(self):
        ''' Cleanup the GPIO before being destroyed '''
        GPIO.cleanup(self.W_CLK)
        GPIO.cleanup(self.FQ_UD)
        GPIO.cleanup(self.DATA)
        GPIO.cleanup(self.RESET)


    def Reset(self):
        GPIO.output(self.RESET,1)  # Reset the chip.
        time.sleep(0.0002)         # Sleep 0.2 ms = 200 ns
        GPIO.output(self.RESET,0)

    def SetFrequency(self,frequency,phase=None):
        ''' Send a new frequency to the device. This assumes it is running
        with a 125 MHz crystal. '''
        self.freq=int(frequency*(2**32)/125000000) # Normalize to crystal frequency
        if phase is not None:
            self.phase=phase
        self.SendData()

    def GetFrequency(self):
        ''' Return the current frequency setting. (not read from device)'''
        return( self.freq*125000000/(2**32))

    def SendData(self):
        '''This actually sends the bits to the device.'''

        # Send serial initialization sequence
        GPIO.output(self.W_CLK,1)
        GPIO.output(self.W_CLK,0)
        GPIO.output(self.FQ_UD,1)
        GPIO.output(self.FQ_UD,0)
        # Send out the 40 bits
        self.SendBits(self.freq,32)
        self.SendBits(0,2)
        self.SendBits(self.powerdown,1)
        self.SendBits(self.phase,5)
        GPIO.output(self.FQ_UD,1)
        # Load the data
        GPIO.output(self.FQ_UD,0)


    def SendBits(self,data,nbits):
        '''Send a sequence of nbits bits from data to output, LSB first.'''

        for i in range(nbits):
            GPIO.output(self.W_CLK,0)  # Make sure clock is low.
            bit = (data & 0b01)
            data >>= 1
            GPIO.output(self.DATA,bit)
            GPIO.output(self.W_CLK,1)  # load the bit.
        GPIO.output(self.DATA,0)
        GPIO.output(self.W_CLK,0)

def main(argv):
    '''Test code for the AD9850 driver.
        If no arguments supplied, assume RESET:22,DATA:23,FQ_UD:24,W_CLK:25'''

    if len(argv)>1:
        assert len(argv)==5
        RESET=int(argv[1])
        DATA =int(argv[2])
        FQ_UD=int(argv[3])
        W_CLK=int(argv[4])
    else:
        RESET = 22
        DATA =  23
        FQ_UD = 24
        W_CLK = 25              			# Define GPIO pins

    AD = AD9850(RESET,DATA,FQ_UD,W_CLK)

    try:
        fr=10
        while True:
            AD.SetFrequency(fr)
            fr+=4
            if fr>10000000:
                fr=10
            time.sleep(0.01)

    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == '__main__':
    import sys
    import time

    main(sys.argv)
