# SPI version of the MCP320x driver.
# NOTE: NOW OBSOLETE. USE THE MCP320x driver directly for SPI
#
# Author: Maurik Holtrop
#
# This module interfaces with the MCP300x or MCP320x family of chips, There
# are 10-bit and 12-bit ADCs respectively.  The x number indicates the number
# of multiplexed analog inputs:  2 (MCP3202), 4 (MCP3204) or 8 (MCP3208)
# Communications with this chip are over the SPI protocol.
# See: https://en.wikipedia.org/wiki/Serial_Peripheral_Interface_Bus
#
# The SPI protocol needed is MODE=0, CPHA=0, which has a positive polarity clock,
# (the clock is 0 at rest, active at 1) and a positive phase (0 to 1 transition) for reading
# or writing the data. This corresponds to the specifications of the MCP320x chips.
#
# From MCP3208 datasheet:
# Outging data : MCU latches data to A/D converter on rising edges of SCLK
# Incoming data: Data is clocked out of A/D converter on falling edges, so should be read on rising edge.
#

import spidev

class MCP320xspi:

    def __init__(self,bus=0,device=0,speed=1000000,single_ended=1,chip='MCP3202'):
        '''Initialize the code and set the GPIO pins.
        The last argument, ch_max, is 2 for the MCP3202, 4 for the
        MCP3204 or 8 for the MCS3208'''

        self._busnum = bus
        self._devnum = device
        self._single_ended=single_ended

        dDict = {
                "MCP3202":
                    {'Channel_Max': 2,
                     'Bit_length' : 12},
                "MCP3204":
                    {'Channel_Max': 4,
                     'Bit_length' : 12},
                "MCP3208":
                    {'Channel_Max': 8,
                     'Bit_length' : 12},
                "MCP3002":
                    {'Channel_Max': 2,
                     'Bit_length' : 10},
                "MCP3004":
                    {'Channel_Max': 4,
                     'Bit_length' : 10},
                "MCP3008":
                    {'Channel_Max': 8,
                     'Bit_length' : 10}
                }

        if chip in dDict:
            self._channel_max = dDict[chip['Channel_Max']]
            self._bit_length = dDict[chip['Bit_length']]
        else:
            print "Unknown chip: {} - Please re-initialize.".format(chip)
            self._channel_max = 0
            self._bit_length  = 0
            return

        if not self._channel_max in [2,4,8]:
            print("ERROR - Chip is 2,4 or 8 channels, cannot use {}".format(self._channel_max))


        self._dev = spidev.SpiDev(self._busnum,self._devnum)
        self._dev.mode =0
        self._dev.max_speed_hz=speed
        self._dev.bits_per_word = 8         # Despite what you may think, 12 does not work.
        self._control0=[0b00000110,0b00100000,0]  # Single ended/Differential needs to be implemented here.

    def __del__(self):
        ''' Cleanup the spidev before being destroyed '''
        self._dev.close()

    def get_channel_max(self):
        return(self._channel_max)

    def get_bit_length(self):
        return(self._bit_lenght)

    def get_max_speed(self):
        return(self._dev.max_speed_hz)

    def set_max_speed(self,speed):
        self._dev.max_speed_hz=speed

    def ReadADC(self,channel):
        '''This method reads the ADC value, after connecting the analog multiplexer to the specified
        channel.
        input:   channel  - selects the channel.
        returns: ADC value is returned as a n-bit integer value, with n=10 or 12 depending on the chip.'''

        if channel < 0 or channel >= self._channel_max:
            print("Error - chip does not have channel = {}".format(channel))
            return(0)

        control=[ self._control0[0] + ((channel&0b100)>>2) , self._control0[1]+((channel&0b011)<<6),0]
        dat = self._dev.xfer(control)
        value= (dat[1]<<8)+dat[2]
        return(value)


    def FastReadADC0(self):
        '''This reads the actual ADC value of channel 0, with as little overhead as possible.
        returns: The ADC value as an n-bit integer value, with n=10 or 12 depending on the chip.'''

        dat = self._dev.xfer(self._control0)
        value= (dat[1]<<8)+dat[2]
        return(value)
