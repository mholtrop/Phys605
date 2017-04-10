#
# This module will steer a MAX7219 chip.
#
# The MAX7219 is an LED driver that can steer 8x 7-segment numerical display, or
# an 8x8 Matrix of LEDs.
#

import RPi.GPIO as GPIO
import time

class MAX7219:

    def __init__(self,CLK_pin,DATA_pin,CS_bar_pin):
        self.CLK = CLK_pin
        self.DATA = DATA_pin
        self.CS_bar = CS_bar_pin

        if GPIO.getmode() != 11:
            GPIO.setmode(GPIO.BCM)

        GPIO.setup(self.CLK,GPIO.OUT)
        GPIO.setup(self.DATA,GPIO.OUT)
        GPIO.setup(self.CS_bar,GPIO.OUT)

        GPIO.output(self.CLK,0)
        GPIO.output(self.DATA,0)
        GPIO.output(self.CS_bar,1)

        self.Init(1)

    def Init(self,mode):
        ''' Initialize the MAX7219 Chip. Mode=1 is for numbers, mode=2 is no-decode'''
        self.WriteLocChar(0x0F,0x01) # Test ON
        time.sleep(0.5)
        self.WriteLocChar(0x0F,0x00) # Test OFF

        self.WriteLocChar(0x0B,0x07) # All 8 digits
        self.WriteLocChar(0x0A,0x0B) # Quite bright
        self.WriteLocChar(0x0C,1) # Set for normal operation.
        if mode == 1:
            self.WriteLocChar(0x09,0xFF) # Decode mode
        else:
            self.WriteLocChar(0x09,0x00) # Raw mode

    def __del__(self):          # This is automatically called when the class is deleted.
        WriteChar(0x0C,0x0) # Turn off
        GPIO.cleanup(self.CLK)
        GPIO.cleanup(self.DATA)
        GPIO.cleanup(self.CS_bar)

    def WriteData(self,data):
        '''Write the 16 bit data to the output '''
        GPIO.output(self.CS_bar,0)

        for i in range(16):  # send out 16 bits.
            GPIO.output(self.CLK,0)
            #time.sleep(0.00001)
            bit = data & 0x8000
            GPIO.output(self.DATA,bit)
            #time.sleep(0.00001)
            GPIO.output(self.CLK,1)
            #time.sleep(0.00001)
            data <<=1
            if(i==7):
                GPIO.output(self.CLK,0)
                GPIO.output(self.DATA,0)
            #    time.sleep(0.00003)

        GPIO.output(self.DATA,0)
        GPIO.output(self.CLK,0)
        GPIO.output(self.CS_bar,1)

    def WriteLocChar(self,loc,dat):
        '''Write dat to loc. If the mode is 1 then dat is a number and loc is the location.
        If mode is 2 then dat is an 8 bit LED position.'''

        out = (loc <<8)
        out += dat
        #out += 0b0000000000000000  # Dummy bits
        self.WriteData(out)

    def WriteInt(self,n):
        ''' Write the integer n on the display '''
        if n > 99999999:
            for i in range(8):
                WriteChar(i+1,0x0A)
            return

        for i in range(8):
            n,d = divmod(n,10)
            if n==0 and d == 0:
                if i==0:
                    self.WriteLocChar(i+1,0x0)  # 0
                else:
                    self.WriteLocChar(i+1,0x0F) # Blank
            else:
                self.WriteLocChar(i+1,d)

    def WriteFloat(self,f):
        '''Write a floating point number. Trying to use a reasonable format '''
        s = "{:9.8g}".format(f)
        #print("Trying to write ",s," len=",len(s))
        if s.count('e')>0 or f<0.01:          # Too big or small for x.x format.
            s = "{:9.4e}".format(f)
        loc = 1
        highbit=0
        rev = reversed(s[0:8+s.count('.')+s.count('e')])
        for c in rev: #Start with the lowest number first.
            if c == '.':
                highbit=1
            else:
                if c.isdigit():
                    i = int(c)
                    i += highbit<<7
                    self.WriteLocChar(loc,i)
                    loc += 1
                    #print("L: {:1d} C: 0x{:2x}".format(loc,i))
                elif c == ' ':
                    self.WriteLocChar(loc,0x0F) # Write blank
                    loc += 1
                    #print("L: {:1d} C: 0x{:2x}".format(loc,0x0F))
                elif c== '+':
                    self.WriteLocChar(loc,0x0B) # Write E
                    loc += 1
                    #print("L: {:1d} C: 0x{:2x}".format(loc,0x0B))
                elif c== '-':
                    self.WriteLocChar(loc,0x0A) # Write -
                    loc += 1
                    #print("L: {:1d} C: 0x{:2x}".format(loc,0x0A))
                elif c== 'e' or c=='E':         # Skip the E, E- too long.
                    pass
                else:
                    print("Bad char in string: ",c)
                highbit=0
