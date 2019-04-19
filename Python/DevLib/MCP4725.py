#!/usr/bin/env python
#
# This driver sets the output on a MCP4725 chip, and also reads back the current setting.
#
# To see if the MCP4725 is available on the bus execute:
#  sudo i2cdetect -y 1
# You should see a grid with all the I2C devices. This device shows up as
# "62" normalle.
#
# Addresses for this device:
# The factory sets the first 4 address bits to 1100, the next three bits are A2,A1,A0
# The A2,A1 bit are determined by the chip model. The normal setting is 01.
# A0 is determined by a pin on the chip, and is set to 0, resulting in address = 0x62
# A jumper on the board allow you to change this from GND (A0=0) to VCC (A0=1).
# If you switch the jumper the normal address will be 0x63
#
# I2C Bus access for Python, see: https://pypi.python.org/pypi/smbus2
#
# Author: Maurik Holtrop
# Based on the datasheet at: https://www.microchip.com/datasheet/MCP4725
# Looked that the AdaFruit code: https://github.com/adafruit/Adafruit_CircuitPython_MCP4725.git
#

import smbus

class MCP4725:
    """
    MCP4725 12-bit digital to analog converter.
    Parameters: bus (default=1), addr (default = 0x62)
    """

    # Global buffer to prevent allocations and heap fragmentation.
    # Note this is not thread-safe or re-entrant by design!
    _BUFFER = bytearray(3)

    def __init__(self, bus=1, address=0x62):
        try:
            self._bus = smbus.SMBus(bus)
        except IOError:
            print("Error opening SMBus {}. Please make sure the Raspberry Pi is setup to read this bus.".format(bus))
            return(None)

        self._address=address            # Set by the hardware = 0b1101000
        self._buf=[]

    def write(self, val):
        pass

    def write_fast_mode(self, val):
        # Perform a 'fast mode' write to update the DAC value.
        # Will not enter power down, update EEPROM, or any other state beyond
        # the 12-bit DAC value.
        assert 0 <= val <= 4095
        try:
            # Make sure bus is locked before write.
            while not self._i2c.try_lock():
                pass
            # Build bytes to send to device with updated value.
            val &= 0xFFF
            self._BUFFER[0] = _MCP4725_WRITE_FAST_MODE | (val >> 8)
            self._BUFFER[1] = val & 0xFF
            self._i2c.writeto(self._address, self._BUFFER, end=2)
        finally:
            # Ensure bus is always unlocked.
            self._i2c.unlock()

    def read_full(self):
        '''
        Perform a read on the device DAC and EEPROM
        Returns: tuple (DAC,EEPROM,STATUS)
        DAC    = current 12 bit value for Vout in the DAC.
        EEPROM = current 12 bit value for Vout in the EEPROM
        STATUS = Bits 3:0 = Ready, Power on Reset, PD1, PD2

        Normal operation will have Ready =1, POR=1, PD1=0, PD2=0
        '''
        vals = self._bus.read_i2c_block_data(self._address,0x0,4)
        status = ((val[0]>>4)&0b00001100) + ((val[0]>>1)&0b00000011)
        dac = (val[1]<<4) +(val[2]>>4)
        eeprom = ((val[3]&0b00001111)<<4) + val[4]
        return(dac,eeprom,status)

    def read(self):
        '''
        Perform a read on the device DAC only.
        Returns: DAC value as 12-bit integer.
        This is equivalent to reading .value
        '''
        val = self._bus.read_i2c_block_data(self._address,0x0,3)
        status = ((val[0]>>4)&0b00001100) + ((val[0]>>1)&0b00000011)
        dac = (val[1]<<4) +(val[2]>>4)
        return(dac)

    def write_eeprom(self,val):
        '''
        Write a new value to the ADC, also updating the value in the EEPROM
        '''
        assert 0 <= val <= 4095
        command = 0b01100000
        hi = (val>>4)
        lo = ((val & 0x0F) << 4)
        self._bus.write_i2c_block_data(self._address,0x0,[0,command,hi,lo])


    def write(self,val):
        '''
        Write a new value to the DAC, setting the Vout to the new value.
        This is equivalent to writing to .value
        '''
        assert 0 <= val <= 4095
        hi = val>>8
        lo = val & 0xFF
        self._bus.write_i2c_block_data(self._address,0x0,[0,hi,lo])


    @property
    def value(self):
        """
        The DAC value. A 12-bit integer.
        """
        return(self.read())

    @value.setter
    def value(self, val):
        assert 0 <= val <= 4095
        self.write(val)

    @property
    def normalized_value(self):
        """The DAC value as a floating point number in the range 0.0 to 1.0.
        """
        return self.read()/4095.0

    @normalized_value.setter
    def normalized_value(self, val):
        assert 0.0 <= val <= 1.0
        raw_value = int(val * 4095.0)
        self.write(raw_value)
