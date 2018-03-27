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
import time

class MCP320xspi:

    def __init__(self,bus=0,device=0,speed=1000000,single_ended=1,chip='MCP3202'):
        '''Initialize the code and set the GPIO pins.
        The last argument, ch_max, is 2 for the MCP3202, 4 for the
        MCP3204 or 8 for the MCS3208'''

        # Set the logger for this file and intialize the level to DEBUG
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)

        # Create the file handler for this logger, sets its level to DEBUG
        file_handler = logging.FileHandler('./logs/mcp320x_{}.log'.format(time.strftime("%d%m%y_%H%M")), delay=False)
        file_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter("%(levelname)s - %(message)s")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        # Add the stream handler so the logger will also output to the console, set
        # the level to debug
        stream_handler = logging.StreamHandler()
        formatter = logging.Formatter("mcp320xspi: %(levelname)s - %(message)s")
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)
        self.log = logger

        self._busnum = bus
        self._devnum = device
        self._single_ended=single_ended

        # Defines a dictionary containing the channnel max 
        # and bit length values for each chip (shortens very long if statement)
        
        chip_dictionary = {"MCP3202": [2, 12], 
                            "MCP3204": [4, 12],
                            "MCP3208": [8, 12],
                            "MCP3002": [2, 10],
                            "MCP3004": [4, 10],
                            "MCP3008": [8, 10]}

        current_chip = chip_dictionary.get(chip)

        if current_chip is not None:
            self._channel_max = current_chip[0]
            self._bit_length = current_chip[1]
        else:
            self.log.warning("Unknown chip: {} - Please re-initialize.")
            self._channel_max = 0
            self._bit_length  = 0
            return

        if not self._channel_max in [2,4,8]:
            self.log.error("ERROR - Chip is 2,4 or 8 channels, cannot use {}".format(self._channel_max))


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
            self.log.error("Error - chip does not have channel = {}".format(channel))
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
