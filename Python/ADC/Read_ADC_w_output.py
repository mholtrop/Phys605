#!/usr/bin/env python
#
# Phys605  Digital Lab 6
#
# Example ADC reading program 2.
#
# This is a slightly improved implementation in Python to read the
# MCP3208 ADC chip.
#
# This implementation moves the work of reading the ADC to a module,
# which was places in the Phys605 directory of your "code" directory.
# This means that the Phys605 directory is 'one up' from the current
# direcotry, or in Unix commandline ".."
#
# As you can see, moving the details of reading the ADC to a module
# cleans up the code for this program. The module can now be used in many
# different programs.
#
# Add ".." to the path for reading modules, so the MCP320x module can be found
import time
import math
import numpy as np
import sys
sys.path.append("..")

from Phys605 import MCP320x  # From the Phys605 dir, load the MCP320x module.
from Phys605 import MAX7219

def Main():
    ''' Example ADC read main function. This will read ONE value from the ADC and print it.'''
    #
    # Clearly, you would need to change this part to suit your needs.
    #
    # The MCP320x module contains the class MCP320x, which we initialize here:
    adc = MCP320x(CS_bar_pin=13,CLK_pin=12,MOSI_pin=6,MISO_pin=5,chip="MCP3202")
    disp = MAX7219(CLK_pin=23,DATA_pin=24,CS_bar_pin=25)
    #
    # Now "adc" is an MCP320x class object, that can read the ADC for us.
    #
    count=0
    loc=0
    #
    # We implement a "circular buffer" that holds N samples that we are averaging over.
    # Each time we update the display, an average is calculated on the buffer values
    # and displayed. This way, you are always getting the average of the last N samples.
    #
    vdata = []
    for i in range(100):
         val = adc.ReadADC(0)
         vdata.append(val)

    while True:
        val = adc.ReadADC(0)   # Read the data from the analog input number 0.
        vdata[loc] = val
        loc += 1

        if loc == len(vdata):
            loc=0
        # Write the value on the MAX7219 display.
        # disp.WriteInt(val)
        if loc%10==0:
            vavg=np.average(vdata)
            vstd=np.std(vdata)
            volts = (vavg/4095.)*3.301
            disp.WriteFloat(volts)

        time.sleep(0.005)
    # Cleanup() Cleanup is now automatic when the adc class is deleted.


# This following bit of code allows you to load this script into Python at the commandline
# or as part of another script, and in those cases NOT execute the Main() function.
# If you execute the script from the command prompt, then the name of the scrtipt will
# be set to __main__, so then execute the Main() function.
if __name__ == "__main__":
    Main()
