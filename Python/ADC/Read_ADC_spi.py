#!/usr/bin/env python
#
# Phys605  Digital Lab 6
#
# Example ADC reading program 4, using MC320xspi module.
#
import sys
sys.path.append("..")

from Phys605 import MCP320xspi  # From the Phys605 dir, load the MCP320x module.


def Main():
    ''' Example ADC read main function. This will read ONE value from the ADC and print it.'''
    #
    # Clearly, you would need to change this part to suit your needs.
    #

    # Define "input" to be Python2 and Python3 compatible.
    try:
        input = raw_input
    except NameError:
        pass


    adc = MCP320xspi(speed=1000000,chip="MCP3208")

    c = ' '
    print("Press enter to read the ADC channels, q<enter> to quit.")
    while c != 'q' and c != 'Q':
        c=input('...')

        for ch in range(adc.get_channel_max()):
            val = adc.ReadADC(ch)   # Read the data from the analog input number 0.
            # Print the value in decimal, hexadecimal, and binary format.
            # Binary format: {:0b} prints the value in 1 and 0,
            print "Ch: {:2d} Value: {:4d} (0x{:04X} = 0b{:012b})".format(ch,val,val,val)


# This following bit of code allows you to load this script into Python at the commandline
# or as part of another script, and in those cases NOT execute the Main() function.
# If you execute the script from the command prompt, then the name of the scrtipt will
# be set to __main__, so then execute the Main() function.
if __name__ == "__main__":
    Main()
