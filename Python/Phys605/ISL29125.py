#!/usr/bin/env python
#
# Class for driving the ISL2915 RGB Light Sensor.
#
# Author: Maurik Holtrop @ University of New Hampshire
#
# Sources used: Sparkfun Arduino Library for ISL2915: https://github.com/sparkfun/SparkFun_ISL29125_Breakout_Arduino_Library/tree/V_1.0.1

import smbus

class ISL29125:

    # Constants from the DATA SHEET.
    # Following the Sparkfun Arduino Driver names.
    #
    # ISL29125 I2C Address
    ISL_I2C_ADDR = 0x44

    # Constants.
    DEVICE_ID_ANSWER = 0x7D
    DEVICE_RESET_COMMAND = 0x46

    # ISL29125 Registers
    DEVICE_ID = 0x00
    CONFIG_1 = 0x01
    CONFIG_2 = 0x02
    CONFIG_3 = 0x03
    THRESHOLD_LL = 0x04
    THRESHOLD_LH = 0x05
    THRESHOLD_HL = 0x06
    THRESHOLD_HH = 0x07
    STATUS = 0x08
    GREEN_L = 0x09
    GREEN_H = 0x0A
    RED_L = 0x0B
    RED_H = 0x0C
    BLUE_L = 0x0D
    BLUE_H = 0x0E

    # Configuration Settings
    CFG_DEFAULT = 0x00

    # CONFIG1
    # Pick a mode, determines what color[s] the sensor samples, if any
    CFG1_MODE_POWERDOWN = 0x00
    CFG1_MODE_G = 0x01
    CFG1_MODE_R = 0x02
    CFG1_MODE_B = 0x03
    CFG1_MODE_STANDBY = 0x04
    CFG1_MODE_RGB = 0x05
    CFG1_MODE_RG = 0x06
    CFG1_MODE_GB = 0x07

    # Light intensity range
    # In a dark environment 375Lux is best, otherwise 10KLux is likely the best option
    CFG1_375LUX = 0x00
    CFG1_10KLUX = 0x08

    # Change this to 12 bit if you want less accuracy, but faster sensor reads
    # At default 16 bit, each sensor sample for a given color is about ~100ms
    CFG1_16BIT = 0x00
    CFG1_12BIT = 0x10

    # Unless you want the interrupt pin to be an input that triggers sensor sampling, leave this on normal
    CFG1_ADC_SYNC_NORMAL = 0x00
    CFG1_ADC_SYNC_TO_INT = 0x20

    # CONFIG2
    # Selects upper or lower range of IR filtering
    CFG2_IR_OFFSET_OFF = 0x00
    CFG2_IR_OFFSET_ON = 0x80

    # Sets amount of IR filtering, can use these presets or any value between = 0x00 and = 0x3F
    # Consult datasheet for detailed IR filtering calibration
    CFG2_IR_ADJUST_LOW = 0x00
    CFG2_IR_ADJUST_MID = 0x20
    CFG2_IR_ADJUST_HIGH = 0x3F

    # CONFIG3
    # No interrupts, or interrupts based on a selected color
    CFG3_NO_INT = 0x00
    CFG3_G_INT = 0x01
    CFG3_R_INT = 0x02
    CFG3_B_INT = 0x03

    # How many times a sensor sample must hit a threshold before triggering an interrupt
    # More consecutive samples means more times between interrupts, but less triggers from short transients
    CFG3_INT_PRST1 = 0x00
    CFG3_INT_PRST2 = 0x04
    CFG3_INT_PRST4 = 0x08
    CFG3_INT_PRST8 = 0x0C

    # If you would rather have interrupts trigger when a sensor sampling is complete, enable this
    # If this is disabled, interrupts are based on comparing sensor data to threshold settings
    CFG3_RGB_CONV_TO_INT_DISABLE = 0x00
    CFG3_RGB_CONV_TO_INT_ENABLE = 0x10

    # STATUS FLAG MASKS
    FLAG_INT = 0x01
    FLAG_CONV_DONE = 0x02
    FLAG_BROWNOUT = 0x04
    FLAG_CONV_G = 0x10
    FLAG_CONV_R = 0x20
    FLAG_CONV_B = 0x30

    def __init__(self):
        '''Initialize the class. Currently no arguments needed.'''

        self._dev = smbus.SMBus(1)

        ans=self._dev.read_i2c_block_data(self.ISL_I2C_ADDR,self.DEVICE_ID,1)
        if( ans[0] != self.DEVICE_ID_ANSWER ):
            print("Device not found at address {}. Device id returned = {}".format(self.ISL_I2C_ADDR,ans[0]))
            return(0)

        self.reset() # Reset all registers to defaut state.

        # Set the device for RGB data, 10k LUX
        self.config( (self.CFG1_MODE_RGB | self.CFG1_10KLUX, self.CFG2_IR_ADJUST_HIGH, self.CFG_DEFAULT) );

    def reset(self):
        ''' Reset all the device control registers to default state = 0 '''
        self._dev.write_byte_data(self.ISL_I2C_ADDR,self.DEVICE_ID,self.DEVICE_RESET_COMMAND)

        dat = []
        for i in range(3):
            dat.append(self._dev.read_byte_data(self.ISL_I2C_ADDR,self.CONFIG_1+i))

        if(sum(dat)!=0):
            print("Device RESET not successful. Please check your device.")
            return(1)

        return(0)

    def config(self,dat):
        ''' Configure the device according to the argument in dat.
        Pass a list with 3 values: (config_1,config_2,config_3) '''

        for i in range(3):
            self._dev.write_byte_data(self.ISL_I2C_ADDR,self.CONFIG_1+i,dat[i])

    def ReadRGB(self):
        ''' Read the G,R,B register (Low,High) and convert to 3 16-bit integers.
        Return: [G, R, B] tuple. Note the order of colors!'''

        # We read 6 bytes starting at GREEN_L = 0x09.
        # This will return [GREEN_L,GREEN_H,RED_L,RED_H,BLUE_L,BLUE_H]
        dat = self._dev.read_i2c_block_data(self.ISL_I2C_ADDR,self.GREEN_L,6)

        # Combine the L and H and put into output

        out = []
        for i in range(3):
            out.append(dat[i*2] + (dat[i*2+1]<<8) )
        return(out)
