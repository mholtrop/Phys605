#
# This module interfaces with the MCP300x or MCP320x family of chips, There
# are 10-bit and 12-bit ADCs respectively.  The x number indicates the number
# of multiplexed analog inputs:  2 (MCP3202), 4 (MCP3204) or 8 (MCP3208)
# Communications with this chip are over the SPI protocol.
# See: https://en.wikipedia.org/wiki/Serial_Peripheral_Interface_Bus
#
# This code does not use the SPI interface of the RPI, instead it uses
# regular GPIO ports. Doing this is colloquially called "bit-banging".
#
# The SPI protocol simulated here is MODE=0, CPHA=0, which has a positive polarity clock,
# (the clock is 0 at rest, active at 1) and a positive phase (0 to 1 transition) for reading
# or writing the data. Thus corresponds to the specifications of the MCP320x chips.
#
# From MCP3208 datasheet:
# Outging data : MCU latches data to A/D converter on rising edges of SCLK
# Incoming data: Data is clocked out of A/D converter on falling edges, so should be read on rising edge.

import RPi.GPIO as GPIO
import time

class MCP320x:

    def __init__(self,CS_bar_pin,CLK_pin,MOSI_pin,MISO_pin,chip='MCP3202'):
        '''Initialize the code and set the GPIO pins.
        The last argument, ch_max, is 2 for the MCP3202, 4 for the
        MCP3204 or 8 for the MCS3208'''

        self.CLK = CLK_pin
        self.MOSI = MOSI_pin
        self.MISO = MISO_pin
        self.CS_bar = CS_bar_pin

        if chip == "MCP3202":
            self.Channel_max = 2
            self.Bit_length  =12
        elif chip == "MCP3204":
            self.Channel_max = 4
            self.Bit_length  =12
        elif chip == "MCP3208":
            self.Channel_max = 8
            self.Bit_length  =12
        elif chip == "MCP3002":
            self.Channel_max = 2
            self.Bit_length  =10
        elif chip == "MCP3004":
            self.Channel_max = 4
            self.Bit_length  =10
        elif chip == "MCP3008":
            self.Channel_max = 8
            self.Bit_length  =10
        else:
            print "Unknown chip: {} - Please re-initialize."
            self.Channel_max = 0
            self.Bit_length  = 0
            return

        if not self.Channel_max in [2,4,8]:
            print("ERROR - Chip is 2,4 or 8 channels, cannot use {}".format(self.Channel_max))

        self.Single_ended_mode = 1;

        if GPIO.getmode() != 11:
            GPIO.setmode(GPIO.BCM)

        GPIO.setup(self.CLK,GPIO.OUT)
        GPIO.setup(self.MOSI,GPIO.OUT)
        GPIO.setup(self.MISO,GPIO.IN)
        GPIO.setup(self.CS_bar,GPIO.OUT)

        GPIO.output(self.CLK,0)
        GPIO.output(self.MOSI,0)
        GPIO.output(self.CS_bar,1)

    def __del__(self):
        ''' Cleanup the GPIO before being destroyed '''
        GPIO.cleanup(self.CS_bar)
        GPIO.cleanup(self.CLK)
        GPIO.cleanup(self.MOSI)
        GPIO.cleanup(self.MISO)

    def SendBit(self,bit):
        ''' Send out a single bit, and pulse clock.'''

        #
        # The input is read on the rising edge of the clock.
        #
        GPIO.output(self.MOSI,bit) # Set the bit.
        GPIO.output(self.CLK,1)    # Rising edge sends data
        GPIO.output(self.CLK,0)    # Return clock to zero.

    def ReadBit(self):
        ''' Read a single bit from the ADC and pulse clock.'''
        #
        # The output is going out on the falling edge of the clock,
        # and is to be read on the rising edge of the clock.

        # Clock should be already low, and data should already be set.
        GPIO.output(self.CLK,1) # Set the clock high. Ready to read.
        bit = GPIO.input(self.MISO) # Read the bit.
        GPIO.output(self.CLK,0) # Return clock low, next bit will be set.

        return(bit)


    def ReadADC(self,channel):
        '''This reads the actual ADC value, after connecting the analog multiplexer to
        channel.
        ADC value is returned at a n-bit integer value, with n=10 or 12 depending on the chip.'''
        if channel < 0 or channel >= self.Channel_max:
            print("Error - chip does not have channel = {}".format(channel))

        # To read out this chip you need to send:
        # 1 - start bit
        # 2 - Single ended (1) or differantial (0) mode
        # 3 - Channel select: 1 bit for x=2 or 3 bits for x=4,8
        # 4 - MSB first (1) or LSB first (0)
        #
        # Start of sequence sets CS_bar low, and sends sequence
        #
        GPIO.output(self.CLK,0)                # Make sure clock starts low.
        GPIO.output(self.MOSI,0)
        GPIO.output(self.CS_bar,0)             # Select the chip.
        self.SendBit(1)                        # Start bit = 1
        self.SendBit(self.Single_ended_mode)   # Select single or differential
        if self.Channel_max > 2:
            self.SendBit(int( (channel & 0b100)>0) ) # Send high bit of channel = DS2
            self.SendBit(int( (channel & 0b010)>0) ) # Send mid  bit of channel = DS1
            self.SendBit(int( (channel & 0b001)>0) ) # Send low  bit of channel = DS0
        else:
            self.SendBit(channel)
        self.SendBit(1)                       # MSB First (for MCP3x02) or don't care.

        # The clock is currently low, and the dummy bit = 0 is on the ouput of the ADC
        #
        dummy = self.ReadBit() # Read the bit.
        #if dummy != 0:
        #    print "We expected a 0, dummy bit but we got a 1. Something is wrong here."
        data = 0
        for i in range(self.Bit_length):
            data <<= 1                     # Note you need to shift left first, or else you shift the last bit (bit 0) to the 1 position.
            bit = self.ReadBit()
            data += bit

        GPIO.output(self.CS_bar,1)  # Unselect the chip.

        return(data)
