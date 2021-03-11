#!/usr/bin/env python
#
# Phys605  Digital Lab 6
#
# Example ADC reading program 4, using MC320xspi module.
#
from DevLib import MCP320x  # From the DevLib, load the MCP320x module.
import time

def Main():
    ''' Example ADC read main function. This will read values from the ADC and print them in a loop.'''
    # Define "input" to be Python2 and Python3 compatible.

    clock_speed = 1000000
    chip_select = 0

    adc = MCP320x(0,clock_speed,chip_select,chip="MCP3208")  # The 0 is there to select the SPI interface.

    try:
        while True:
            for ch in range(adc.get_channel_max()):
                val = adc.read_adc(ch)   # Read the data from the analog input number 0.
                # Print the value in decimal, hexadecimal, and binary format.
                # Binary format: {:0b} prints the value in 1 and 0,
                print("Ch: {:2d} Value: {:4d} (0x{:04X} = 0b{:012b})".format(ch,val,val,val))
            print("")
            time.sleep(0.5)

    except KeyboardInterrupt:
        sys.exit(0)



# This following bit of code allows you to load this script into Python at the commandline
# or as part of another script, and in those cases NOT execute the Main() function.
# If you execute the script from the command prompt, then the name of the scrtipt will
# be set to __main__, so then execute the Main() function.
if __name__ == "__main__":
    Main()
