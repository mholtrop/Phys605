#!/usr/bin/env python
#
# APA102 Driver
#
# Author: Maurik Holtrop
#
# This module is a pure Python version to write to the APA102 LEDS.
#
#
# Inspired by Martin Erzberger's version: https://github.com/tinue/APA102_Pi/blob/master/apa102.py
# and https://github.com/adafruit/Adafruit_CircuitPython_NeoPixel/blob/master/neopixel.py
# But is a complete re-implementation, using numpy.ndarray as the base class.
#
# APA102 Datasheet:
# AdaFruit info: https://learn.adafruit.com/adafruit-dotstar-leds
#
# A note on these LEDS:
# Despite what the AdaFruit folks say, you *can* actually control this type of LED with 3.3V logic.,
# just not very well. This works best if you run the LEDS at 3.3V, though they will not be quite as bright, they
# will work OK and can be tested in that mode.
# However, if you want this to run glitch free at high data rates and full brightness, 5V power and logic are recommended.
#
try:
    import RPi.GPIO as GPIO
except:
    pass
try:
    import Adafruit_BBIO as GPIO
except:
    pass

try:
    import spidev
    import BBSpiDev
except:
    pass

import colorsys
import numpy as np
from math import ceil

class APA102(np.ndarray):
    """
    Driver for APA102 LEDS using the numpy.ndarray as a base class.
    This means that the class fully behaves like a numpy array, and thus has
    all the features that numpy array permit. The LEDS can thus be structured as
    a strip, or 2-D (or 3-D) array, and numpy operations work on this array.

    :param input        - Standard np.ndarray for initialization,
                          or a shape, (8,8) for an 8x8.
    :param CS           - Dummy - not used by APA102 LEDS, so set to None.
                          If set to 0 or 1, the HW CS will be used. You can use an NAND gate
                          and an INVERTER to effectively add a CS line to the APA102 string.
    :param CLK          - For HW SPI this is the clock speed.
                          For Software SPI, this it the PIN with the clock signal.
    :param MOSI         - GPIO pin number for data out. Use None for hardware SPI.

    Example code:

    .. code-block:: python

        from DevLib import APA102
        a =  APA102((8,8),CLK=16,MOSI=17)
        # color every row in an increasing blue color.
        a[:]=[a.rgb((0.,0.,i/200.)) for i in range(8)]
        a.show()
    """

    def __new__(cls,input, CS=None,CLK=None,MOSI=None):
        """Inialize the APA102 class.

        param: input        - Standard np.ndarray for initialization,
                              or a shape, (8,8) for an 8x8.
        param: CS           - Dummy - not used by APA102 LEDS, so set to None.
                              If set to 0 or 1, the HW CS will be used. You can use an NAND gate
                              and an INVERTER to effectively add a CS line to the APA102 string.
        param: CLK          - For HW SPI this is the clock speed.
                              For Software SPI, this it the PIN with the clock signal.
        param: MOSI         - GPIO pin number for data out. Use None for hardware SPI.
        """

        # Input array is an already formed ndarray instance
        # We first cast to be our class type
        if isinstance(input,np.ndarray):
            obj = np.asarray(input,dtype=np.int32).view(cls)
        else:
            obj = np.asarray(np.zeros(shape=input, dtype=np.int32)).view(cls)

        # Add new attributes
        obj._MOSI = MOSI
        obj._CS   = CS
        obj._CLK  = CLK
        obj._dev = None
        obj._brightness = 31

        return(obj)

    def __array_finalize__(self,obj):
        """ Special numpy call that finalizes the object.
        See: https://docs.scipy.org/doc/numpy/user/basics.subclassing.html
        on why."""
        if obj is None: return

        self._MOSI = getattr(obj,'_MOSI',None)
        self._CS   = getattr(obj,'_CS',  None)
        self._CLK  = getattr(obj,'_CLK', None)
        self._dev =  getattr(obj,'_dev', None)
        self._brightness = getattr(obj,'_brightness',None)

    def __init__(self,input_array, CS=None,CLK=None,MOSI=None):
        """ Initialization that only gets called for new instances, not copies.
            Here we setup the SPI device."""

#        self._brightness = getattr(self,"_brightness",31)  # If not set, set to 31

        if self._MOSI is None:
            if self._CLK is None or self._CLK < 1:
                self._CLK=1000000
            if self._CS is None:
                self._CS = 0 # Hardware must have the CS.
            # Initialize the SPI hardware device
            self._dev = spidev.SpiDev(0,self._CS)
            self._dev.max_speed_hz = self.CLK
        else:
            self._dev = BBSpiDev.BBSpiDev(self._CS,self._CLK,self._MOSI,None)

    def __str__(self):
        out="[\n"
        if self.ndim == 1:
            for x in self:
                out+="({:03x},{:03x},{:03x},{:03x}) ".format((x>>24)&0xFF,x&0xFF,(x>>8)&0xFF,(x>>16)&0xFF)
            out =out + "]"
            return(out)
        if self.ndim == 2:
            for x in self:
                out = out+"["
                for y in x:
                    out+="({:03x},{:03x},{:03x},{:03x}) ".format((y>>24)&0xFF,y&0xFF,(y>>8)&0xFF,(y>>16)&0xFF)
                out = out+"]\n"
            out = out + "]"
            return(out)

    @property
    def brightness(self):
        """Global brightness for LEDS"""
        return(self._brightness)

    @brightness.setter
    def brightness(self,level):
        self._brightness = (level & 0x1F)

    def close(self):
        """Explicitly close the SPI device. """
#        self._dev.close()

    def Add(self,value):
        """Add value to each LED. Value is an encoded rgb value.
        This can also be accomplished with a.ravel()[:] += value """
        self.ravel()[:] += value

    def zero(self):
        """Set all the LEDS to zero, i.e. dark, but do not call show() """
        self.fill(0)

    def clear(self):
        """ Turns off the strip and shows the result right away."""
        self.zero()
        self.show()

    def set_pixel(self, loc, col, bright=1.):
        """Sets the color of one pixel in the LED stripe.
        params:
        loc    :  The location of the led to set. Can be an int
                  or an (x,y) location, depending on initialization.
        col    :  if col is an integer -> an rgb HEX color value.
               :  if col is tuple      -> (r,g,b) HEX triplet.
        bright :  The overall brightness fraction of global_brightness.
                  1. = MAX brightness.

        This sets the pixel in the leds array. Pixels will be shown with
        the show() function.
        """
        # Calculate pixel brightness as a percentage of the
        # defined global_brightness. Round up to nearest integer
        # as we expect some brightness unless set to 0
        brightness = int(ceil(bright*self._brightness/100.0))
        # LED startframe is three "1" bits, followed by 5 brightness bits

        if type(col) is list or type(col) is tuple:
            rgb_color = self.rgb(col,brightness)
        elif type(col) is int:
            rgb_color = col + ((brightness<<24)&0x1F)
        else:
            raise ValueError("set_pixel requires an integer or (r,g,b) tuple")

        self.itemset(loc,rgb_color)

    def show(self):
        """Sends the content of the pixel buffer to the strip.
        Todo: More than 1024 LEDs requires more than one xfer operation.
        """
        self._dev.writebytes([0]*4) # Write 32 zeros for the start frame.

        # We need to unpack the array of 32bit ints into 8bit bytes, because
        # spidev can only handle 8bit byte arrays. You can can do this the slow
        # way as:
        # for x in self.ravel():
        #     for i in [(x>>24)&0xFF,(x>>16)&0xFF,(x>>8)&0xFF,x&0xFF]:
        #       vals.append(i)
        # It is faster/simpler to use list comprehension, in this case
        # a nested list comprehension.
        # In the process we create a copy, which for spidev is good thing.
        # If you run the clock at 8MHz, it takes 6 to 7 ms for show() with 256 LEDs on an RPi3.
        # SPI takes up to 4096 Integers. So we are fine for up to 1024 LEDs.
        self._dev.writebytes([ int(i) for x in self.ravel() for i in [(0xe0|((x>>24)&0x1F)),(x>>16)&0xFF,(x>>8)&0xFF,x&0xFF]])
        # To ensure that all the data gets to all the LEDS, we need to
        # continue clocking. The easiest way to do so is by sending zeros.
        # Round up num_led/2 bits (or num_led/16 bytes)
        self._dev.writebytes([0]*((self.size + 15) // 16))


    def cleanup(self):
        """Release the SPI device; Call this method at the end"""
        self._dev.close()  # Close SPI port

    def rgb(self,t,bright_level=None):
        """Make one 3*8 byte color value from an (r,g,b) tuple
        of HEX r,g,b values, i.e. (r,g,b) are 8-bit integers [0,255]"""
        if bright_level is None:
            bright_level = self.brightness
        if len(t) == 4:
            bright_level = t[3] # Overwrite
        return(((bright_level&0x1F)<<24)+((t[2]&0xFF)<<16)+((t[1]&0xFF)<<8)+(t[0]&0xFF))

    def to_rgb(self,x):
        """Go from a 32 bit color value to (red,green,blue) hex values."""
        return([x&0xFF,(x>>8)&0xFF,(x>>16)&0xFF])

    def to_rgbl(self,x):
        """Go from a 32 bit color value to (red,green,blue,level) hex values."""
        return([x&0xFF,(x>>8)&0xFF,(x>>16)&0xFF,((x>>24)&0x1F)])

    def rgb_dec(self,t,bright_level=None):
        """Make one 3*8 byte color value from a decimal (r,g,b) tuple
        of float r,g,b values, i.e. (r,g,b) are [0.,1.]"""
        if bright_level is not None:
            bright_level = int(bright_level*31)&0x1F
        return(self.rgb([ int(i*255)&0xFF for i in t],bright_level))

    def hls(self,t,bright_level=None):
        """Make one 3*8 byte color value from an (h,l,s) tuple.
        Note that (h,l,s) are [0.,1.0], floats between 0 and 1."""
        if bright_level is not None:
            bright_level *= 31

        return(self.rgb_dec(colorsys.hls_to_rgb(t[0],t[1],t[2]),bright_level))

def main(argv):

    import time
    if len(argv) < 3:
        clk_pin=1000000
        mosi_pin=0
    else:
        clk_pin = int(argv[1])
        mosi_pin= int(argv[2])

    print("APA102 Test code.")
    a = APA102((8,8),MOSI=mosi_pin,CLK=clk_pin)
    a.brightness = 5
    # Horizontal fade
    a[:] = [a.rgb((0,0,i*16)) for i in range(1,9)]
    a.show()
    time.sleep(3)
    a.transpose()[:]=[a.rgb((i*16,0,0)) for i in range(8,0,-1)]
    a.show()
    time.sleep(3)
    red=np.outer(np.arange(7,-1,-1),np.arange(0,8))
    blue=np.outer(np.arange(0,8),np.arange(0,8))
    green=np.outer([4]*8,np.arange(7,-1,-1))
    a[:,:] = a.rgb((red,green,blue,10))
    print(a)
    a.show()
    time.sleep(3)
    a.clear()

if __name__ == '__main__':
    import sys
    main(sys.argv)
