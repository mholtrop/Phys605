#!/usr/bin/env python
#
# MCP320x
#
# Author: Maurik Holtrop
#
# This module interfaces with the MCP300x or MCP320x family of chips. These
# are 10-bit and 12-bit ADCs respectively.  The x number indicates the number
# of multiplexed analog inputs:  2 (MCP3202), 4 (MCP3204) or 8 (MCP3208)
# Communications with this chip are over the SPI protocol.
# See: https://en.wikipedia.org/wiki/Serial_Peripheral_Interface_Bus
#
# The version of the code has two SPI interfaces: the builtin hardware
# SPI interface on the RPI, or a "bit-banged" GPIO version.
#
# Bit-Bang GPIO:
#   We emulate a SPI port in software using the GPIO lines.
#   This is a bit slower than the hardware interface, but it is far more
#   clear what is going on, plus the RPi has only one SPI device.
#   Connections: RPi GPIO to  MCP320x
#              CS_bar_pin = CS/SHDN
#              CLK_pin    = CLK
#              MOSI_pin   = D_in
#              MISO_pin   = D_out
#
# Hardware SPI:
#   This uses the builtin hardware on the RPi. You need to enable this with the
#   raspi-config program first. The data rate can be up to 1MHz.
#   Connections: RPi pins to MCP320x
#              CE0 or CE1 = CS/SHDN  (chip select) set CS_bar = 0 or 1
#              SCK        = CLK      set CLK_pin  = 1000000 (transfer speed)
#              MOSI       = D_in     set MOSI_pin = 0
#              MISO       = D_out    set MISO_pin = 0

# The SPI protocol simulated here is MODE=0, CPHA=0, which has a positive polarity clock,
# (the clock is 0 at rest, active at 1) and a positive phase (0 to 1 transition) for reading
# or writing the data. Thus corresponds to the specifications of the MCP320x chips.
#
# From MCP3208 datasheet:
# Outging data : MCU latches data to A/D converter on rising edges of SCLK
# Incoming data: Data is clocked out of A/D converter on falling edges, so should be read on rising edge.

import RPi.GPIO as GPIO
import spidev

class MCP320x:

    def __init__(self,CS_bar_pin,CLK_pin=1000000,MOSI_pin=0,MISO_pin=0,chip='MCP3208',
                 channel_max=None,bit_length=None,single_ended=1):
        '''Initialize the code and set the GPIO pins.
        The last argument, ch_max, is 2 for the MCP3202, 4 for the
        MCP3204 or 8 for the MCS3208'''

        self.CLK = CLK_pin
        self.MOSI = MOSI_pin
        self.MISO = MISO_pin
        self.CS_bar = CS_bar_pin

        chip_dictionary={
                "MCP3202":(2,12),
                "MCP3204":(4,12),
                "MCP3208":(8,12),
                "MCP3002":(2,10),
                "MCP3004":(4,10),
                "MCP3008":(8,10)
        }

        if chip in chip_dictionary:
            self.Channel_max = chip_dictionary[chip][0]
            self.Bit_length  = chip_dictionary[chip][1]
        elif chip == None and (channel_max is not None) and (bit_length is not None):
            self.Channel_max = channel_max
            self.Bit_length  = bit_length
        else:
            print("Unknown chip: {} - Please re-initialize.")
            self.Channel_max = 0
            self.Bit_length  = 0
            return

        self.Single_ended_mode = single_ended;

        # This is used to speed up the SPIDEV communication. Send out MSB first.
        # control[0] - bit7-3: upper 5 bits 0, because we can only send 8 bit sequences.
        #            - bit2   : Start bit - starts conversion in ADCs
        #            - bit1   : Select single_ended=1 or differential=0
        #            - bit0   : D2 high bit of channel select.
        # control[1] - bit7   : D1 middle bit of channel select.
        #            - bit6   : D0 low bit of channel select.
        #            - bit5-0 : Don't care.
        if self.Single_ended_mode==0:
            self._control0=[0b00000100,0b00100000,0]  # Pre-compute part of the control word.
        else:
            self._control0=[0b00000110,0b00100000,0]  # Pre-compute part of the control word.

        if self.MOSI > 0:  # Bing Bang mode
            assert self.MISO !=0 and self.CLK < 32
            if GPIO.getmode() != 11:
                GPIO.setmode(GPIO.BCM)        # Use the BCM numbering scheme

            GPIO.setup(self.CLK,GPIO.OUT)     # Setup the ports for in and output
            GPIO.setup(self.MOSI,GPIO.OUT)
            GPIO.setup(self.MISO,GPIO.IN)
            GPIO.setup(self.CS_bar,GPIO.OUT)

            GPIO.output(self.CLK,0)           # Set the clock low.
            GPIO.output(self.MOSI,0)          # Set the Master Out low
            GPIO.output(self.CS_bar,1)        # Set the CS_bar high

        else:
            self._dev = spidev.SpiDev(0,self.CS_bar) # Start a SpiDev device
            self._dev.mode = 0                    # Set SPI mode (phase)
            self._dev.max_speed_hz = self.CLK     # Set the data rate
            self._dev.bits_per_word = 8           # Number of bit per word. ALWAYS 8

    def __del__(self):
        ''' Cleanup the GPIO before being destroyed '''
        if(self.MOSI>0):
            GPIO.cleanup(self.CS_bar)
            GPIO.cleanup(self.CLK)
            GPIO.cleanup(self.MOSI)
            GPIO.cleanup(self.MISO)

    def get_channel_max(self):
        '''Return the maximum number of channels'''
        return(self.Channel_max)

    def get_bit_length(self):
        '''Return the number of bits that will be read'''
        return(self.Bit_length)

    def get_value_max(self):
        '''Return the maximum value possible for an ADC read'''
        return(2**self.Bit_length-1)

    def SendBit(self,bit):
        ''' Send out a single bit, and pulse clock.'''
        if self.MOSI == 0:
            return
        #
        # The input is read on the rising edge of the clock.
        #
        GPIO.output(self.MOSI,bit) # Set the bit.
        GPIO.output(self.CLK,1)    # Rising edge sends data
        GPIO.output(self.CLK,0)    # Return clock to zero.

    def ReadBit(self):
        ''' Read a single bit from the ADC and pulse clock.'''
        if self.MOSI == 0:
            return 0
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
        the desired channel.
        ADC value is returned at a n-bit integer value, with n=10 or 12 depending on the chip.
        The value can be converted to a voltage with:
           volts = data*Vref/(2**n-1)'''
        if channel < 0 or channel >= self.Channel_max:
            print("Error - chip does not have channel = {}".format(channel))


        if self.MOSI == 0:
            # SPIdev Code
            # This builds up the control word, which selects the channel
            # and sets single/differential more.
            control=[ self._control0[0] + ((channel&0b100)>>2) , self._control0[1]+((channel&0b011)<<6),0]
            dat = self._dev.xfer(control)
            value= (dat[1]<<8)+dat[2] # Unpack the two 8-bit words to a single integer.
            return(value)

        else:
            # Bit Bang code.
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

    def FastReadADC0(self):
        '''This reads the actual ADC value of channel 0, with as little overhead as possible.
        Use with SPIDEV ONLY!!!!
        returns: The ADC value as an n-bit integer value, with n=10 or 12 depending on the chip.'''

        dat = self._dev.xfer(self._control0)
        value= (dat[1]<<8)+dat[2]
        return(value)

def main(argv):
    '''Test code for the MCP320x driver. This assumes you are using a MCP3208
    If no arguments are supplied, then use SPIdev for CE0 and read channel 0'''

    if len(argv) < 2:
        cs_bar=0
        clk_pin=1000000
        mosi_pin=0
        miso_pin=0
        channel =0
    elif len(argv) < 6:
        print("Please supply: cs_bar_pin clk_pin mosi_pin miso_pin channel")
        sys.exit(1)

    else:
        cs_bar  = int(argv[1])
        clk_pin = int(argv[2])
        mosi_pin= int(argv[3])
        miso_pin= int(argv[4])
        channel = int(argv[5])

    A = MCP320x(cs_bar,clk_pin,mosi_pin,miso_pin)
    try:
        while True:
            value=A.ReadADC(channel)
            print("{:4d}".format(value))
            time.sleep(0.1)
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == '__main__':
    import sys
    import time

    main(sys.argv)
