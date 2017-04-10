#!/usr/env python
#
# Phys605  Digital Lab 6
#
# Example ADC reading program 1.
#
# This is a simple implementation in Python to read the
# MCP3208 ADC chip.

import RPi.GPIO as GPIO
import time

MISO   =  5     # Goes to Dout pin on chip.
MOSI   =  6     # Goes to Din  pin on chip.
CLK    = 12     # Clock - CLK  pin on chip.
CS_bar = 13     # Select- CS-bar pin on chip.

Channel_max = 8
Bit_length  =12

Single_ended_mode = 1;

def Init():
    GPIO.setmode(GPIO.BCM)

    GPIO.setup(CLK,GPIO.OUT)
    GPIO.setup(MOSI,GPIO.OUT)
    GPIO.setup(MISO,GPIO.IN)
    GPIO.setup(CS_bar,GPIO.OUT)

    GPIO.output(CLK,0)
    GPIO.output(MOSI,0)
    GPIO.output(CS_bar,1)

def Cleanup():
    ''' Cleanup the GPIO before being destroyed '''
    GPIO.cleanup(self.CS_bar)
    GPIO.cleanup(self.CLK)
    GPIO.cleanup(self.MOSI)
    GPIO.cleanup(self.MISO)

def SendBit(bit):
    ''' Send out a single bit, and pulse clock.'''
    #
    # The input is read on the rising edge of the clock.
    #
    GPIO.output(MOSI,bit) # Set the bit.
    GPIO.output(CLK,1)    # Rising edge sends data
    GPIO.output(CLK,0)    # Return clock to zero.

def ReadBit(self):
    ''' Read a single bit from the ADC and pulse clock.'''
    #
    # The output is going out on the falling edge of the clock!
    #
    GPIO.output(CLK,1) # Set the clock highbit
    GPIO.output(CLK,0) # Falling clock receives data.
    bit = GPIO.input(MISO) # Read the bit.
    return(bit)

def ReadADC(self,channel):
    '''This reads the actual ADC value, after connecting the analog multiplexer to
    channel.
    ADC value is returned at a n-bit integer value, with n=10 or 12 depending on the chip.'''
    if channel < 0 or channel >= Channel_max:
        print("Error - chip does not have channel = {}".format(channel))

    # To read out this chip you need to send:
    # 1 - start bit
    # 2 - Single ended (1) or differantial (0) mode
    # 3 - Channel select: 3 bits
    # 4 - MSB first (1) or LSB first (0)
    #
    # Start of sequence sets CS_bar low, and sends sequence
    #
    GPIO.output(CS_bar,0)             # Select the chip.
    SendBit(1)                        # Start bit = 1
    SendBit(Single_ended_mode)   # Select single or differential
    SendBit(int( (channel & 0b100)>0) ) # Send high bit of channel = DS2
    SendBit(int( (channel & 0b010)>0) ) # Send mid  bit of channel = DS1
    SendBit(int( (channel & 0b001)>0) ) # Send low  bit of channel = DS0
    SendBit(1)                          # Dummy high

    # The clock is currently low, and the dummy bit = 0 is on the ouput of the ADC
    #
    dummy = GPIO.input(MISO) # Read the bit.
    data = 0
    for i in range(Bit_length):
        data <<= 1                     # Note you need to shift left first, or else you shift the last bit (bit 0) to the 1 position.
        bit = ReadBit()
        data += bit

    GPIO.output(CS_bar,1)  # Unselect the chip.

    return(data

def Main():
    ''' Example ADC read main function. This will read ONE value from the ADC and print it.'''
    #
    # Clearly, you would need to change this part to suit your needs.
    #
    Init()              # Load data into the shifters.
    val = ReadADC(0)   # Read the data from the analog input number 0.

    # Print the value in decimal, hexadecimal, and binary format.
    # Binary format: {:0b} prints the value in 1 and 0,
    print "Value: {:4d} (0x{:04X} = 0b{:012b})".format( val,val,val)

    Cleanup()



# This following bit of code allows you to load this script into Python at the commandline
# or as part of another script, and in those cases NOT execute the Main() function.
# If you execute the script from the command prompt, then the name of the scrtipt will
# be set to __main__, so then execute the Main() function.
if __name__ == "__main__":
    Main()
