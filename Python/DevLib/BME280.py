#!/usr/bin/env python
#
# BME280/BMP280 Sensor module
#
# Author: Maurik Holtrop
#
# This module interfaces over the I2C bus with an BMP280 or BME280 sensor.
# The only difference between these sensors is that the BME also includes a
# humidity sensor, while the BMP version has only temperature and pressure.
#
# I2C bus:
# You can check for the presense of this detector on the I2C bus with the command:
# "i2cdetect 1", which returns a table of addresses. This sensor is at 76 (HEX)
#
# Datasheet: https://www.bosch-sensortec.com/bst/products/all_products/bme280
# Official C reference driver: https://www.bosch-sensortec.com/bst/products/all_products/bme280
#
# Hookup of breakout board:
# Most breakout boards bring out the VCC, GND, SCL, SDA, CSB and SDO
# The VCC and GND are obviously for the power (3.3V) and ground.
# The SCL is the CLOCK, connect this to the SCK.
# The SDA on the board is SDI on the chip. It is data in/out for I2C
# (It is also data in for SPI, but this driver does not support SPI at the moment.)
# The CSB is chip select bar, it also selects between I2C and SPI. For I2C it needs to be pulled high, to VCC
# during power up. If not, the device will be locked in SPI mode.
# The SDO pin is used to select the address. If low, the address is 1110110 (0x76), if high 1110111 (0x77).
# In SPI mode, the SDO pin is used as the SPI data output.
#
# The output of this code was compared 1 to 1 with the BME280_FLOAT_ENABLE version of the
# C master driver provided by Bosch.

import smbus
import time
from ctypes import c_short
from ctypes import c_byte
from ctypes import c_ubyte

class BME280:

    # Table of useful address locations.
    _DEVICE_ID  = 0xD0
    _CONFIG_REG = 0xF5
    _CONTROL_REG= 0xF4
    _STATUS_REG = 0xF3
    _CONTROL_HUM= 0xF2
    _DEV_READ_ADDRESS = 0xF7
    _DEV_READ_LEN=8

    def __init__(self,address=0x76,bus=1):
        '''Initialize the class. The arguments: I2C address, which is either 0x76 (SDO pin low)
        or 0x77 (SDO pin high), and bus, which is 1 for RPi and can be 0,1,2 for BeagleBone'''

        self._dev = smbus.SMBus(bus)
        self._dev_address = address
        # Get the device ID from the device.
        self._dev_id =self._dev.read_byte_data(self._dev_address,self._DEVICE_ID)
        self._config =self._dev.read_byte_data(self._dev_address,self._CONFIG_REG)
        self._control=self._dev.read_byte_data(self._dev_address,self._CONTROL_REG)
        if self._dev_id == 0x60:
            self._control_hum=self._dev.read_byte_data(self._dev_address,self._CONTROL_HUM)
        else:
            self._config_hum=0
        self._temp_fine = 0
        self._raw_temp=0
        self._raw_pres=0
        self._raw_humi=0
        self.temperature=0
        self.pressure=0
        self.humidity=0

        if self._dev_id == 0x58: # Device is a BMP280
            self._DEV_READ_LEN=6

        self.Read_Calibrations() # Get the device calibrations. Only needed once.

    def Reset(self):
        '''Perform a soft reset of the chip. All registers will go to their default value'''
        self._dev.write_byte_data(self._dev_address,0xE0,0xB6)

    def Configure(self):
        '''After a reset or power cycle, load the most basic settings.'''
        self.Set_Filter(1)
        self.Set_Oversampling((1,1,1))
        self.Set_Standby_Time(500)

    def Get_Mode(self):
        '''Return the operation mode of the device.
        Valid modes: 0 = sleep mode, 1 or 2 = forced mode, 3 = normal mode.'''
        self._control=self._dev.read_byte_data(self._dev_address,self._CONTROL_REG)
        return(self._control&0b011)

    def Set_Mode(self,mode):
        '''Set the operation mode for the device.
        Valid modes: 0 = sleep mode, 1 or 2 = forced mode, 3 = normal mode.'''
        if mode<0 or mode >3:
            print("ERROR: Invalid mode requested.")
        self._control = (self._control & 0b11111100) | mode
        self._dev.write_byte_data(self._dev_address,self._CONTROL_REG,self._control)

    def Get_Status(self):
        '''Get the device status bits:
        bit0 = "Non Volatile Memory read/write in progress"
        bit3 = "Measurement conversion in progress"
        Other bits are not defined.'''
        status=self._dev.read_byte_data(self._dev_address,self._STATUS_REG)
        return(status)

    def Get_Oversampling(self):
        '''Read the control register of the device and return the oversampling rates
        as (Oversample Temp, Oversample Press,Oversample Humidity)
        Note that a value of 0 (zero) means the measurement is skipped.'''
        codes={0:0,1:1,2:2,3:4,4:8,5:16,6:16,7:16}
        self._control=self._dev.read_byte_data(self._dev_address,self._CONTROL_REG)
        osrs_t = (self._control&0b11100000)>>5
        osrs_p = (self._control&0b00011100)>>2
        if self._dev_id == 0x60:
            self._control_hum=self._dev.read_byte_data(self._dev_address,self._CONTROL_HUM)
            osrs_h = (self._control_hum&0b00000111)
        else:
            osrs_h = 0
        self._oversample = (codes[osrs_t],codes[osrs_p],codes[osrs_h])
        return(self._oversample)

    def Set_Oversampling(self,oversample):
        '''Set the oversampling rates for (temperature,pressure,humidity).
        Valid oversampling rates are 0,1,2,4,8,16 '''
        codes={0:0,1:1,2:2,4:3,8:4,16:5}
        if oversample[0] in codes:
            osrs_t = codes[oversample[0]]
        else:
            print("Error: Invalid oversampling code for temperature.")

        if oversample[1] in codes:
            osrs_p = codes[oversample[1]]
        else:
            print("Error: Invalid oversampling code for pressure.")

        if oversample[2] in codes:
            osrs_h = codes[oversample[2]]
        else:
            print("Error: Invalid oversampling code for humidity.")

        # According to the data sheet, the humidity control must be written to first.
        if self._dev_id == 0x60:
            self._control_hum = osrs_h
            self._dev.write_byte_data(self._dev_address,self._CONTROL_HUM,self._control_hum)

        self._control=self._dev.read_byte_data(self._dev_address,self._CONTROL_REG)
        self._control = (self._control&0b011) | (osrs_t <<5) | (osrs_p) <<2
        self._dev.write_byte_data(self._dev_address,self._CONTROL_REG,self._control)

    def Get_Filter(self):
        '''Return the IIR filter setting.
         A value of 0 means the filter is off.'''

        self._config =self._dev.read_byte_data(self._dev_address,self._CONFIG_REG)
        filter= (2**(self._config&0b111))
        return(filter)

    def Set_Filter(self,filter):
        '''Set the IIR filter length for temperature and pressure measurementsself.
        Valid settings are 1,2,4,8,16'''
        bits=filter.bit_length()-1;  # This is a log2 cheat
        self._config =self._dev.read_byte_data(self._dev_address,self._CONFIG_REG)
        self._config = (self._config & 0b11111000) | (bits & 0b00000111)
        self._dev.write_byte_data(self._dev_address,self._CONFIG_REG,self._config)

    def Get_Standby_Time(self):
        '''Read the standby time code from the device and translate it to a standby time in ms.'''
        self._config = self._dev.read_byte_data(self._dev_address,self._CONFIG_REG)
        stb_code = (self._config& 0b11100000)>>5
        if self._dev_id == 0x60:
            codes={0b000:0.5,0b110:10.,0b111:20.,0b001:62.5,0b010:125.,0b011:250.,0b100:500.,0b101:1000.}
        else:
            codes={0b000:0.5,0b001:62.5,0b010:125.,0b011:250.,0b100:500.,0b101:1000.,0b110:2000.,0b111:4000.}

        self._standby_time = codes[stb_code]
        return(self._standby_time)

    def Set_Standby_Time(self,stb_time):
        '''When running in normal mode, set the standby time, t_sb, which is the time
        the sensor waits between measurements.
        Only a limited set of values are possible:
        If any other value is chosen, this routine will choose the nearest possible value.
        Returns: Actual value used.'''

        if self._dev_id == 0x60:
            codes={0.5:0b000,10.:0b110,20.:0b111,62.5:0b001,125.:0b010,250.:0b011,500.:0b100,1000.:0b101}
        else:
            codes={0.5:0b000,62.5:0b001,125.:0b010,250.:0b011,500.:0b100,1000.:0b101,2000.:0b110,4000.:0b111}

        # Now find the value that is closest to the one requestsed:
        diff = min([ abs(x-stb_time) for x in codes.keys()])
        if stb_time+diff in codes:
            self._standby_time = stb_time+diff
        elif stb_time-diff in codes:
            self._standby_time = stb_time+diff
        else:
            print("Error: Could not set standby time to ",stb_time)

        stb_code = codes[self._standby_time]
        self._config = self._dev.read_byte_data(self._dev_address,self._CONFIG_REG)
        self._config = (self._control & 0b00011111) | (stb_code << 5)
        self._dev.write_byte_data(self._dev_address,self._CONFIG_REG,self._config)

        return(self._standby_time)

    def Estimate_Measurement_Time(self):
        '''Calcuate an estimate for the typical measurement time, and the max measurement time.
        returns: (t_typ,t_max) in ms'''
        t_typ = 1.+ 2.*self._Oversampling_T + 2.*self._Oversampling_P + 0.5 + 2.*self._Oversampling_H + 0.5
        t_max = 1.25+ 2.3*self._Oversampling_T + 2.3*self._Oversampling_P + 0.575 + 2.3*self._Oversampling_H + 0.575
        return(t_typ,t_max)

    def Read_Calibrations(self):
        '''Read and store the calibration data from the device.
        This is needed for the corrections to the raw values from the device.'''

        # Read the two data blocks.
        Calbuf1 = self._dev.read_i2c_block_data(self._dev_address,0x88,26)
        Calbuf2 = self._dev.read_i2c_block_data(self._dev_address,0xE1,8)

        # Parse the pairs into signed short integers (int16_t).
        # The first 3 are for temperature, the next 9 are for pressure.
        self._Cal_T = [ c_short((Calbuf1[i*2+1]<<8) + Calbuf1[i*2]).value for i in range(3)]
        # Fixup the unsigned shorts (uint16_t)
        self._Cal_T[0]=(Calbuf1[1]<<8) + Calbuf1[0]

        self._Cal_P = [ c_short((Calbuf1[i*2+1]<<8) + Calbuf1[i*2]).value for i in range(3,len(Calbuf1)//2)]
        self._Cal_P[0]=(Calbuf1[7]<<8) + Calbuf1[6]

        # The humidity numbers are in the second block, except the first number.
        # These numbers are packed more complicated.
        self._Cal_H=[]
        self._Cal_H.append(Calbuf1[25])
        self._Cal_H.append(c_short((Calbuf2[1]<<8) + Calbuf2[0]).value)
        self._Cal_H.append(Calbuf2[2])
        self._Cal_H.append(c_short( (Calbuf2[3]<<4) | (Calbuf2[4] & 0x0F) ).value)
        self._Cal_H.append(c_short( (Calbuf2[5]<<4) | (Calbuf2[4] >> 4  ) ).value)
        self._Cal_H.append(c_byte(  Calbuf2[6]).value)

    def Read_Data_Raw(self):
        '''Internal method that reads the raw data from the device and returns it as a list,
        containting: [Raw Temperature,Raw Pressure, Raw Humidity]'''
        dat=self._dev.read_i2c_block_data(self._dev_address,self._DEV_READ_ADDRESS,self._DEV_READ_LEN)
        # Data is packed in MSB,LSB,XLSB order, where only the top 4 bits of XLSB are valid.
        self._raw_pres= ((dat[0]&0xFF)<<12) | ((dat[1]&0xFF)<<4) | ((dat[2]&0xFF)>>4)
        self._raw_temp= ((dat[3]&0xFF)<<12) | ((dat[4]&0xFF)<<4) | ((dat[5]&0xFF)>>4)
        if self._dev_id == 0x60:  # Read humidity MSB,LSB
            self._raw_humi= ((dat[6]&0xFF)<<8) | (dat[7]&0xFF)

        return((self._raw_temp,self._raw_pres,self._raw_humi))

    def Correct_Temp(self,raw_temp):
        '''Internal method, given the raw temperature measurement, use the calibrat
        data to calculate a corrected temperature. Temperature is returned in C.
        Resolution is 0.01 Degree C.
        Also sets _temp_fine, which is needed for the pressure correction.'''
        # From the datasheet:
        #var1 = ((raw_temp>>3) - (self._Cal_TP[0]<<1)) * (self._Cal_TP[1]>> 11)
        #var2 = ((((raw_temp>>4) - self._Cal_TP[0]) * ((raw_temp>>4) - self._Cal_TP[0])) >> 12)*self._Cal_TP[2]>>14
        #self._temp_fine = var1+var2
        #self.Temp = ((self._temp_fine * 5 + 128)>>8)/100.0

        # From the reference driver:
        # Note: calib_data->dig_T1 -> self._Cal_T[0]
        var1 = (raw_temp/ 16384.0 - self._Cal_T[0]/ 1024.0) * (self._Cal_T[1]);
        var2 = (raw_temp/ 131072.0 - (self._Cal_T[0])/8192.0);
        var2 = (var2 * var2) * self._Cal_T[2]
        self._temp_fine = int(var1+var2)
        self.temperature = (var1+var2)/5120.0
        return(self.temperature)

    def Correct_Pressure(self,raw_pres):
        '''Internal method, given a raw pressure measurement, use the calibration
        data to calculate a corrected pressure. Pressure is returned as a float in
        millibar = hPa = 100 Pa.
        This method uses the internal _temp_fine variable, so call Correct_Temp() first.'''
        # From the reference driver:
        # Note: calib_data->dig_T1 -> self._Cal_T[0]
        #       calib_data->dig_P1 -> self._Cal_P[0]
        pressure_min = 30000.0;
        pressure_max = 110000.0;

        var1 = (self._temp_fine / 2.0) - 64000.0
        var2 = var1 * var1 * self._Cal_P[5] / 32768.0
        var2 = var2 + var1 * self._Cal_P[4] * 2.0
        var2 = (var2 / 4.0) + self._Cal_P[3] * 65536.0
        var3 = self._Cal_P[2] * var1 * var1 / 524288.0
        var1 = (var3 + self._Cal_P[1] * var1) / 524288.0
        var1 = (1.0 + var1 / 32768.0) * self._Cal_P[0]
        # avoid exception caused by division by zero
        # print("var1: ",var1,var2,var3)
        if var1==0:
            return(0)

        self.pressure = 1048576.0 - raw_pres
        self.pressure = (self.pressure - (var2 / 4096.0)) * 6250.0 / var1
        var1 = self._Cal_P[8] * self.pressure * self.pressure / 2147483648.0
        var2 = self.pressure * self._Cal_P[7] / 32768.0
        self.pressure = self.pressure + (var1 + var2 + self._Cal_P[6]) / 16.0
        if self.pressure < pressure_min:
            self.pressure = pressure_min
        elif self.pressure > pressure_max:
            self.pressure = pressure_max

        return self.pressure/100.

    def Correct_Humidity(self,raw_humi):
        '''Internal method, given a raw humidity measurement, use the calibration data
        to calculate a corrected humidy. Humidity is returned as a float in % relative humidity.
        This method uses the internal _temp_fine variable, so call Correct_Temp() first.'''

        var1 = (self._temp_fine) - 76800.0;
        var2 = (self._Cal_H[3] * 64.0 + (self._Cal_H[4]/ 16384.0) * var1);
        var3 = raw_humi - var2;
        var4 = self._Cal_H[1] / 65536.0;
        var5 = (1.0 + (self._Cal_H[2] / 67108864.0) * var1);
        var6 = 1.0 + (self._Cal_H[5] / 67108864.0) * var1 * var5;
        var6 = var3 * var4 * (var5 * var6);
        self.humidity = var6 * (1.0 - self._Cal_H[0] * var6 / 524288.0);

        if self.humidity<0:
            self.humidity=0
        if self.humidity>100:
            self.humidity=100

        return self.humidity

    def Read_Data(self):
        '''Read the Temperature, Pressure and Humidity (if BME device) from the device,
        and return the calibrated values.
        If the mode of the device is "Sleep", then a measurement is triggered and the
        method will wait for conversion. If the device in in "Forced", then wait for
        conversion and then read the registers.
        If the mode is "Normal", then the registers are read immediately.
        The accuracy of the numbers will depend on the oversampling settings for the device.'''

        mode=self.Get_Mode()
        if mode == 0:
            self.Set_Mode(1)     # Trigger a measurement.
            mode=1
        if mode==1 or mode ==2:   # Wait for conversion.
            while self.Get_Mode()>0:
                time.sleep(0.001)

        # Ready - Read and process the data.
        raw=self.Read_Data_Raw()
        temp = self.Correct_Temp(raw[0])
        press= self.Correct_Pressure(raw[1])
        if self._dev_id == 0x60:
            humi = self.Correct_Humidity(raw[2])
        else:
            humi=0

        return((temp,press,humi))

def main():
    '''Main code for testing.'''

    bme = BME280()
    bme.Set_Oversampling((16,16,16))
    (temp,press,humi)=bme.Read_Data()
    print(" {:^7}    {:^8}    {:^7}".format("Temp [C]","Press [Pa]","Humidity [%]"))
    print(" {:>7.3f}    {:>8.2f}    {:>7.2f}".format(temp,press,humi))

if __name__ == '__main__':
    main()
