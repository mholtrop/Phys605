#!/usr/bin/env python
#
# The wiringPi requires you to run as sudo.
# This is needed for access to /dev/mem, which we don't use here.
# There is no way around this though, so we start this code as a root user.
#
#
import wiringpi as wp
#
# Define a function to decode BCD encoded numbers.
def decBCD(num):
    return( (num/16)*10 + (num%16) )
#
# Open the RTC
#
fc= wp.wiringPiI2CSetup(0x68)
#
# We read the registers one at a time.
secs = wp.wiringPiI2CReadReg8(fc,0x00)
mins = wp.wiringPiI2CReadReg8(fc,0x01)
hour = wp.wiringPiI2CReadReg8(fc,0x02)
day  = wp.wiringPiI2CReadReg8(fc,0x03)
dat = wp.wiringPiI2CReadReg8(fc,0x04)
mon = wp.wiringPiI2CReadReg8(fc,0x05)
yr = wp.wiringPiI2CReadReg8(fc,0x06)
cent = wp.wiringPiI2CReadReg8(fc,0x07)
temp1 = wp.wiringPiI2CReadReg8(fc,0x11)
temp2 = wp.wiringPiI2CReadReg8(fc,0x12)

year = decBCD(yr)
month = decBCD(mon & 0x7f)
date = decBCD(dat)

if (mon & 0x80)>0:
    year+=2100
else:
    year+=2000

if (hour&0x40)>0: # Test for 12 or 24 hour clock. 1=12 hour 0=24 hour
    hours = decBCD(hour&0x1F)
    if (hour&0x20)>0:
        ampm = "PM"
    else:
        ampm = "AM"
    print "{2}:{1:02d}:{0:02d} {3} ({4}) {5}-{6}-{7}".format(decBCD(secs),decBCD(mins),hours,ampm,day,year,month,date)
else:
    hours = decBCD(hour&0x3F)
    print "{2}:{1:02d}:{0:02d} ({3}) {4}-{5}-{6}".format(decBCD(secs),decBCD(mins),hours,day,year,month,date)
