#!/usr/bin/env python
#
# Phys605  Digital Lab 6
#
# Example ADC reading program 4, using MC320xspi module.
#
import sys
sys.path.append("..")
from Phys605 import MCP320xspi  # From the Phys605 dir, load the MCP320x module.

import matplotlib
matplotlib.use('Agg')
import pylab

import numpy as np

import time

def Main():
    ''' Example ADC read main function. This will read ONE value from the ADC and print it.'''
    #
    # Clearly, you would need to change this part to suit your needs.
    #
    adc = MCP320xspi(speed=1000000,chip="MCP3208")


    Num_Read = 100000
    data=np.zeros(Num_Read)

    now = time.time()
    for i in range(Num_Read):
        data[i] = adc.FastReadADC0()   # Read the data from the analog input number 0.

    dtime=time.time() - now
    print("Time for {} reads: {} = {} Hz".format(Num_Read,dtime,Num_Read/dtime))

    #    pylab.plot(np.linspace(0.,dtime,Num_Read),data)
    #    pylab.savefig("curve.png")

    for t,d in zip(np.linspace(0.,dtime,Num_Read),data):
        print("{},{}".format(t,d))
        
# This following bit of code allows you to load this script into Python at the commandline
# or as part of another script, and in those cases NOT execute the Main() function.
# If you execute the script from the command prompt, then the name of the scrtipt will
# be set to __main__, so then execute the Main() function.
if __name__ == "__main__":
    Main()
