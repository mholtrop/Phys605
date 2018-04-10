#!/usr/bin/env python
#
# This driver code reads a DS3231 based Real Time Clock (RTC) chip.
# The DS3231 is a clock chip with a buildin crystal, which simplifies the design
# of an RTC and makes it more accurate (Accuracy +/-2ppm from 0C to +40C)
# See the datasheet.
#
# To see if the DS3231 is available on the bus execute:
#  sudo i2cdetect -y 1
#
# I2C Bus access for Python, see: https://pypi.python.org/pypi/smbus2/0.2.0
#
# Author: Maurik Holtrop
#
# Notes on reading from the i2C bus:
#
#  The block read will read 32 bytes from the bus, starting at the given address.
#  Reading buf = bus.read_i2c_block_data(0x68,0) - This gets 32 bytes.
#  This block read takes about 5.26 ms (%timeit gives best of 3 at 3.26ms)
#  Reading a sinlge byte take 0.772 ms (%timeit gives best of 3 at 0.684ms)
#  Reading dat2 =[ bus.read_byte_data(0x68,i) for i in range(18)] takes 12.4 ms
#  Reading the time only: dat2 =[ bus.read_byte_data(0x68,i) for i in range(6)] takes 4.23 ms
#
#  So, if you read only part of the time, you are quicker reading bytes.
#
# ADDRESS   BIT 7 MSB   BIT 6   BIT 5   BIT 4   BIT 3   BIT 2   BIT 1   BIT 0 LSB   FUNCTION    RANGE
# 00h           0            10 Seconds       -            Seconds                  Seconds    00-59
# 01h           0            10 Minutes       |             Minutes                 Minutes     00-59
# 02h           0      12/24  AM/PM    10 Hour|              Hour                   Hours   1-12 + AM/PM 00-23
#                            20 Hour
# 03h           0        0       0       0      0     |       Day                   Day         1-7
# 04h           0        0    10 Date         |             Date                    Date        01-31
# 05h       Century      0      0   10 Month  |             Month                   Month/ Century 01-12 + Century
# 06h                      10 Year            |             Year                    Year        00-99
# 07h         A1M1          10 Seconds        |             Seconds                 Alarm 1 Seconds 00-59
# 08h         A1M2          10 Minutes        |             Minutes                 Alarm 1 Minutes 00-59
# 09h         A1M3    12/24 AM/PM   10 Hour   |             Hour                    Alarm 1 Hours   1-12 + AM/PM 00-23
#                           20 Hour
# 0Ah         A1M4    DY/DT   10 Date         |             Day                     Alarm 1 Day     1-7
#                                                           Date                    Alarm 1 Date    1-31
# 0Bh         A2M2          10 Minutes        |             Minutes                 Alarm 2 Minutes 00-59
# 0Ch         A2M3   12/24  AM/PM  10 Hour    |             Hour                    Alarm 2 Hours   1-12 + AM/PM 00-23
#                           20 Hour
# 0Dh         A2M4  DY/DT   10 Date           |             Day                     Alarm 2 Day     1-7
#                                                           Date                    Alarm 2 Date    1-31

# ADDRESS   BIT 7 MSB   BIT 6   BIT 5   BIT 4   BIT 3   BIT 2   BIT 1   BIT 0 LSB   FUNCTION    RANGE
# 0Eh           EOSC    BBSQW   CONV    RS2     RS1     INTCN   A2IE    A1IE        Control
# 0Fh           OSF	  0     0        0      EN32kHz   BSY    A2F     A1F        Control/Status
# 10h           SIGN    DATA    DATA    DATA    DATA    DATA    DATA    DATA        Aging Offset
# 11h           SIGN    DATA    DATA    DATA    DATA    DATA    DATA    DATA        MSB of Temp
# 12h           DATA    DATA    0       0       0       0       0       0           LSB of Temp
#
import time
from datetime import datetime
import smbus


class DS3231:
    def __init__(self,bus=1,address=0x68):
        '''This class opens the I2C bus using smbus and then reads the DS3231 RTC chip
        which should be at address 0x68 on I2C channel 1 for a Raspberry Pi.
        '''
        try:
            self._bus = smbus.SMBus(bus)
        except IOError:
            print("Error opening SMBus {}. Please make sure the Raspberry Pi is setup to read this bus.".format(bus))
            return(None)

        self._address=address            # Set by the hardware = 0b1101000
        self._buf=[]
        self.Read_Buffer() # Test read 32-bytes.

    def bcd(self,b):
        '''Decode the BCD encoded number b into a normal int.'''
        return( (b>>4)*10 + (b&0xF))

    def to_bcd(self,d):
        '''Encode the integer d to bcd.'''
        return( (d//10)*16 + d%10 )

    def Read_Buffer(self):
        '''Read the entire buffer of 18 bytes from the DS3231 using a single 32-word read.'''
        try:
            self._buf = self._bus.read_i2c_block_data(self._address,0x0) # Read 32 bytes of data and put in the clock.
        except IOError:
            print("Error reading from address {}, make sure the DS3231 is properly connected.".format(self._address))
            return(None)

        return(self._buf)

    def GetDateTime(self):
        '''Return the date and time in a datetime structure. '''
        buf = self.Read_Buffer()
        # class datetime.datetime(year, month, day[, hour[, minute[, second[, microsecond[, tzinfo]]]]])
        year = 2000 + (buf[0x05]>>7)*100 + self.bcd(buf[0x06])
        month= self.bcd(buf[0x05]&0x7F)
        day  = self.bcd(buf[0x04])
        if (buf[0x02] & 0b01000000)>0 : # Clock is in 12 hour mode.
            hour = self.bcd(buf[0x02]&0x1F) + 12*(buf[0x02]&0b00100000>0)  # If PM add 12 hours.
        else:
            hour = self.bcd(buf[0x02]&0x3F)
        mins = self.bcd(buf[0x01])
        secs = self.bcd(buf[0x00])
        dattim = datetime(year,month,day,hour,mins,secs)
        return(dattim)

    def GetTemp(self):
        '''Read the temperature of the DS3231, and return the result in centigrade'''
        MSB_temp = self._bus.read_byte_data(self._address,0x11)
        LSB_temp = self._bus.read_byte_data(self._address,0x12)
        return(MSB_temp + 0.25*((LSB_temp)>>6) )

    def Set32kHz(self):
        '''Set the 32k output pin to oscillate a square wave at about 32kHz'''


    def SetToNow(self):
        '''Set the DS3231 to the current time of the RPi. datetime.datetime.now() '''
        self.SetTime(datetime.now())

    def SetTimeUTCNow(self):
        '''Set the DS3231 to the current time in UTC timezone. datetime.datetime.utcnow() '''
        self.SetTime(datetime.utcnow())


    def SetTime(self,dattime):
        '''Set the DS3231 to the datetime in the argument. '''

        year = dattime.year
        cent_bit = (year-2000)//100
        year = self.to_bcd(year%100)
        month= self.to_bcd(dattime.month) + cent_bit * 0b01000000
        day = self.to_bcd(dattime.day)
        weekday= dattime.weekday()
        hours = self.to_bcd(dattime.hour)
        mins  = self.to_bcd(dattime.minute)
        secs  = self.to_bcd(dattime.second)
        buf_out=[secs,mins,hours,weekday,day,month,year]
        for i in range(len(buf_out)):
            self._bus.write_word_data(self._address,i,buf_out[i])

    def SetAlarm1(self,dattime):
        '''Set the alarm1 on the DS3231. '''
        print("Implement me!")

    def SetAlarm2(self,dattime):
        '''Set the alarm2 on the DS3231. '''
        print("Implement me!")

def main(argv):
    '''Test code for the DS3231 driver.
    This will simply print the time and the temperature as provided by the device.'''

    T = DS3231()
    dt = T.GetDateTime()
    temp=T.GetTemp()
    print("It is now {} UTC".format(dt.strftime("%c")))
    print("Temp: {:6.3f}C".format(temp))


if __name__ == '__main__':
    import sys
    import time

    main(sys.argv)
