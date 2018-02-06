#!/usr/bin/env python
#
# This is a test code for reading out the BMP280 over the I2C bus on
# a Raspberry Pi 3. The code uses the WiringPi (Python binding to wiringpi)
# library to communicate over I2C.
#
# Author: Maurik Holtrop - University of New Hampshire
#
import wiringpi as wp
#
class BMP280:
    def __init__(self,devid=0x76):
        '''Initialze the I2C port with wiringpi and start the BMP280 sensor.
        Arguments: devid = the device ID of the sensor, defaults to 0x76'''

        wp.wiringPiSetupGpio()                 # Use the GPIO numbering scheme.
        self.fh = wp.wiringPiI2CSetup(devid)   # Open com to devide
        dat =  wp.wiringPiI2CReadReg8(self.fh,0xD0) # Check device ID
        if dat != 0x58:
            print('''The device at address 0x{:02x} returned 0x{:02x} instead of 0x58.\n
            Probably this is the wrong device.'''.format(devid,dat))
            return(0)

        wp.wiringPiI2CWriteReg8(self.fh,0xF4,0b00100111) # Set for normal operation, 1x oversampling.
        
