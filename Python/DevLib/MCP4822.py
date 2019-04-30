#!/usr/bin/env python
#
# This is a driver for the MCP4822 12-bit SPI DAC
#
# The code can easily be adapted to the MCP48x1 and MCP48x2 and MCP49x1 and MCP49x2 chips,
# but I don't happen to have any of those right now :-)
#
# Author: Maurik Holtrop
#
# Reference: https://www.microchip.com/wwwproducts/en/MCP4822
#
# The device has one 16-bit register:
#  A/B | - | GA | Shutdown | D11 | D10 ... D0
#
# Bit 15:  0 write to A, 1 write to B
# Bit 14:  don't care
# Bit 13:  Output Gain: 0 = 2x,  1 = 1x
# Bit 12:  Shutdown:  0 = Shutdown,  1 = Active output
# Bit 11-0: Data in MSB first format.
#
# The output voltage will be Vout = Gain*( Vref*D/4096)  with Vref = 2.048 V
#
try:
    import RPi.GPIO as GPIO
except:
    try:
        import Adafruit_BBIO as GPIO
    except:
        raise("Could not find a GPIO library")

import spidev
from DevLib import BBSpiDev

class MCP4822(object):

    #
    # Embedded class to modify list behavior. This allows the main class
    # to detect if the user sets or gets the DAC values.
    #
    class my_values(list):
        """Class for setting the value of the chip, which mimics a list."""
        def __init__(self,vals,parent):
            self._parent = parent
            super(MCP4822.my_values,self).__init__(vals)

        def __getitem__(self,idx):
            return(super(MCP4822.my_values,self).__getitem__(idx))

        def __setitem__(self,idx,val):
            assert 0 <= idx <= 1
            assert 0 <= val <= 4095
            hi = (idx<<7) | (self._parent._Gain << 5) | (1 << 4)
            hi |=  (val>>8) & 0x0F
            lo = (val & 0xFF)
            self._parent._dev.writebytes([hi,lo])

            return(super(MCP4822.my_values,self).__setitem__(idx,val))

    class my_volts:
        """Class for relating the value of the chip to volts, which mimics a list."""
        def __init__(self,parent):
            self._parent = parent
            self._n = 0

        def __getitem__(self,idx):
            return(self._parent._tovolt(self._parent._Value[idx]))

        def __setitem__(self,idx,val):
            self._parent._Value[idx]=self._parent._fromvolt(val);

        def __len__(self):
            return(len(self._parent._Value))

        def __iter__(self):
            self._n=0
            return(self)

        def __next__(self):
            if self._n < len(self):
                result = self[self._n]
                self._n += 1
                return(result)
            else:
                raise StopIteration

        def __repr__(self):
            return("Volts: "+str(self))

        def __str__(self):
            tmplist = [ x for x in self ]
            return(str(tmplist))


    def __init__(self,CS_bar_pin,CLK_pin=10000000,MOSI_pin=None,LDAC_pin=None):
        '''Initialize the code and set the GPIO pins.
        If MOSI_pin = None or 0, the code assumes hardware SPI mode, in which case the
        CLK_pin number is taken as the maximum clock speed desired.
        If LDAC=None, then it is assumed the LDAC pin is tied to GND.
        Parameters:
        ------------
        CS_bar_pin = 0 or 1 for SPI, or GPIO pin for CS_bar
        CLK_pin    = Frequency for SPI or GPIO pin for Clock (SCK)
        MOSI_pin   = None for SPI or GIO pin for MOSI or SDI (Data)
        LDAC_pin   = None if tied to ground or GPIO pin for LDAC_bar
        '''

        self._CLK = CLK_pin
        self._MOSI = MOSI_pin
        self._CS_bar = CS_bar_pin
        self._LDAC  = LDAC_pin
        self._Gain  = 1
        self._Value = self.my_values([0,0],self)  # The device does not allow you to read back the value, so we store it.
        self._Volts = self.my_volts(self)

        if self._MOSI == 0:
            self._MOSI = None

        if self._MOSI:  # Bing Bang mode
            self._dev = BBSpiDev(CS=self._CS_bar,CLK=self._CLK,MOSI=self._MOSI,MISO=None)
            self._MaxWriteSpeed=10000000
        else:
            self._dev = spidev.SpiDev(0,self._CS_bar)     # Start a SpiDev device
            self._MaxWriteSpeed=CLK_pin

        self._dev.mode = 0                           # Set SPI mode (phase)
        self._dev.max_speed_hz = self._MaxWriteSpeed  # Set the data rate
        self._dev.bits_per_word = 8                  # Number of bit per word. ALWAYS 8

    def __del__(self):
        ''' Cleanup the GPIO before being destroyed '''
        self._dev.close()

    def _tovolt(self,val):
        """Convert val to volts """
        return(2.048*self._Gain*val/4096)

    def _fromvolt(self,val):
        """Convert val from volt to code"""
        return(int(4096*val/2.048)//(self._Gain))


    @property
    def gain(self):
        """The gain setting, either 1 or 2 """
        return(self._Gain)

    @gain.setter
    def gain(self,val):
        assert 0 < val < 3
        self._Gain = val

    def SetOutput(self,value,channel):
        """Set the output of channel (0=A or 1=B) to value, where value = 0 to 4095 """
        self._Value[channel] = value

    @property
    def values(self):
        """Current values (between 0 and 4095) on channels as a list."""
        return(self._Value)

    @values.setter
    def values(self,v):
        """Set the output value from a list of size 2.
        If only one value is given, set both outputs to that value. """
        if isinstance(v,(int,float)):
            v=[int(v),int(v)]

        assert len(v) == 2

        for i in range(2):
            self._Value[i]= v[i]

    @property
    def volts(self):
        """Current voltage on channels as a list."""
        return(self._Volts)

    @volts.setter
    def volts(self,volt):
        """Set the voltage output from a list of size 2 of float numbers.
        If only one value is given, set both outputs to that value. """
        if isinstance(volt,(int,float)):
            volt=[float(volt),float(volt)]

        assert len(volt) == 2

        for i in range(2):
            self._Volts[i]=volt[i]


def main(argv):
    '''Test code for the MCP4822 driver.
    If no arguments are supplied, then use SPIdev for CE0 and sets voltages on
    both channel A and channel B.
    '''

    import time
    import math

    if len(argv) < 2:
        cs_bar=0
        clk_pin=1000000
        mosi_pin=0
        channel =0
    elif len(argv) < 3:
        print("Please supply: cs_bar_pin clk_pin mosi_pin")
        sys.exit(1)

    else:
        cs_bar  = int(argv[1])
        clk_pin = int(argv[2])
        mosi_pin= int(argv[3])


    dac = MCP4822(cs_bar,clk_pin,mosi_pin)
    dac.gain=2  # allow for volts up to 4V.
    dac.volts[0]=1. # Set output voltage individually
    dac.volts[1]=2.
    time.sleep(10)
    try:
        for i in range(100000):
            v1 = 1.5*math.sin(math.pi*i/30)+1.5
            v2 = 1.5*math.cos(math.pi*i/30)+1.5
            dac.volts=[v1,v2]  # Set by voltage simultaneously.

        dac.values[0]=100  # Set by value individually
        dac.values[1]=200
        time.sleep(10)
        dac.values = [0,0] # Set by value simultaneously
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == '__main__':
    import sys

    main(sys.argv)
