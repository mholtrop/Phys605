#!/usr/bin/env python
#
# This module will steer a MAX7219 chip.
#
# The MAX7219 is an LED driver that can steer 8x 7-segment numerical display, or
# an 8x8 Matrix of LEDs.
#
# Author: Maurik Holtrop
#
import RPi.GPIO as GPIO
from spidev import SpiDev
import time

class MAX7219:
    def __init__(self,DATA_pin,CLK_pin,CS_bar_pin,mode=1):
        '''This class helps with driving a MAX7219 LED module using either regular
        GPIO pins, or SPI hardware interface.
        For SPI hardware, set DATA_pin=0, CS_bar_pin=0 or 1, CLK_pin= bus speed (1000000)
        For GPIO "bit-bang" interface, set DATA_pin = Data in (dat),
        CS_bar = to Chip Select (cs), and CLK_pin= Clock (clk)
        A final argument, mode=1 (default) sets number decoding, while
        mode=0 sets raw mode, see the MAX7219 chip data sheet.
        -------
        This code expects the pin numbers in the BSM standard.
        The Raspberry Pi interfacing is done through the RPi.GPIO module
        or the spi module'''

        self.DATA = DATA_pin
        self.CS_bar = CS_bar_pin
        self.CLK = CLK_pin
        self.Mode = mode
        self._dev = None

        if self.DATA>0:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.CLK,GPIO.OUT)
            GPIO.setup(self.DATA,GPIO.OUT)
            GPIO.setup(self.CS_bar,GPIO.OUT)

            GPIO.output(self.CLK,0)
            GPIO.output(self.DATA,0)
            GPIO.output(self.CS_bar,1)
        else:
            if self.CLK < 100:
                self.CLK=1000000
            self._dev = SpiDev(0,self.CS_bar)
            self._dev.mode =0
            self._dev.max_speed_hz=self.CLK
            self._dev.bits_per_word = 8
        self.Init(mode)

    def Init(self,mode):
        ''' Initialize the MAX7219 Chip. Mode=1 is for numbers, mode=2 is no-decode.
        This will send an initialization sequence to the chip.
        With an __init__ this method is already called.'''
        self.WriteLocChar(0x0F,0x01) # Test ON
        time.sleep(0.5)
        self.WriteLocChar(0x0F,0x00) # Test OFF

        self.WriteLocChar(0x0B,0x07) # All 8 digits
        self.WriteLocChar(0x0A,0x0B) # Quite bright
        self.WriteLocChar(0x0C,1) # Set for normal operation.
        if mode == 1:
            self.Mode=1
            self.WriteLocChar(0x09,0xFF) # Decode mode
        else:
            self.Mode=0
            self.WriteLocChar(0x09,0x00) # Raw mode

        self.Clear()

    def __del__(self):          # This is automatically called when the class is deleted.
        '''Delete and cleanup.'''
        self.WriteLocChar(0x0C,0x0) # Turn off
        if self.DATA>0:
            GPIO.cleanup(self.CLK)
            GPIO.cleanup(self.DATA)
            GPIO.cleanup(self.CS_bar)
        else:
            self._dev.close()

    def Clear(self):
        '''Clear the display to all blanks. (it looks off) '''
        for i in range(8):
            if self.Mode == 1:
                self.WriteLocChar(i+1,0x0F) # Blank
            else:
                self.WriteLocChar(i+1,0x00) # Blank

    def SetBrightness(self,B):
        '''Set the display brightness to B, where 0<=B<16'''
        B = B & 0x0F
        self.WriteLocChar(0x0A,B) # Set brightness

    def WriteData(self,data):
        '''Write the 16 bit data to the output using SPI or
         "bit-banged" SPI on the GPIO output line.
        This is a "raw" mode write, used internally in these methods.'''
        if self.DATA>0:
            GPIO.output(self.CS_bar,0)

            for i in range(16):  # send out 16 bits of data sequentially.
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
        else:
            self._dev.writebytes([(data>>8)&0xFF,data&0xFF]) # Write the first and second byte from data.

    def WriteLocChar(self,loc,dat):
        '''Write dat to loc. If the mode is 1 then dat is a number and loc is the location.
        If mode is 2 then dat is an 8 bit LED position.
        This is used internally to display the numbers/characters.'''
        if self.DATA>0:
            out = (loc <<8)
            out += dat
            #out += 0b0000000000000000  # Dummy bits
            self.WriteData(out)
        else:
            self._dev.writebytes([loc,dat])

    def WriteInt(self,n):
        ''' Write the integer n on the display, shifted left. If n is larger (smaller) than
        fits, an overflow is indicated by all dash.'''

        if self.Mode != 1:
            raise ValueError();

        if n > 99999999 or n< -9999999: # Display overflow, --------
            for i in range(8):
                self.WriteLocChar(i+1,0x0A)
            return

        if n < 0:
            negative=True
            n= -n
        else:
            negative=False
        for i in range(8):
            n,d = divmod(n,10)
            if n==0 and d == 0:
                if i==0:
                    self.WriteLocChar(i+1,0x0)  # 0
                else:
                    if negative:
                        self.WriteLocChar(i+1,0x0A)
                        negative=False
                    else:
                        self.WriteLocChar(i+1,0x0F) # Blank
            else:
                self.WriteLocChar(i+1,d)

    def WriteFloat(self,f,form='{:9.6f}'):
        '''Write a floating point number. Trying to use a reasonable format.
        You can specify the format with the form= argument, using the python
        style, to use with form="{:4.2f}" or form="{:8.4e}" '''

        if self.Mode != 1:
            raise ValueError();

        s = form.format(f)
        loc = 1
        highbit=0
        rev = reversed(s[0:8+s.count('.')+s.count('e')]) # Read the letters reversed, starting at the end.
#        print("Trying to write [{}] len={}".format(s,len(s)))
#        rev_test=""
        for c in rev:       # Get each of the numbers/symbols, starting with the rightmost.
#            rev_test += c
            if c == '.':    # If it is the period, then set bit7 but don't count as a digit.
                highbit=1
            else:
                if c.isdigit():  # It is a digit.
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
        while loc<9:                    # Fill the end with blanks
            self.WriteLocChar(loc,0x0F) # Write blank
            loc += 1


    def __str__(self):
        '''Write something comforting to the user :-) '''
        if self.DATA>0:
            print("MAX7219 driver interface. GPIO mode: DATA={} CS_bar={} CLK={}",self.DATA,self.CS_bar,self.CLK)

#
# The code below turns this module into a program as well
# allowing you to run it in test mode from the command line.
#
def main(argv):
    '''Test the functioning of the module displaying
    the number 12345678, and then counting down.
    The code will use:
    Data pin   = 4
    CLK pin    = 5
    CS_bar pin = 6
    '''
    Max_data   = 4
    Max_clock  = 5
    Max_cs_bar = 6

# If you connect your display to the PSI interface, comment the lines above and uncomment the lines below.
# Max_data = 0        # Use 0 for SPI connection, otherwise use GPIO pin connected to driving
# Max_clock= 1000000  # Use clock frequency for SPI connection, otherwise use GPIO pin connected to CLK
# Max_cs_bar = 0      # Use channel (CE0 or CE1) for SPI connection, otherwise use GPIO pin for CS

    M = MAX7219(Max_data,Max_clock,Max_cs_bar)
    num = 12345678
    M.WriteInt(num)
    time.sleep(1)
    try:
        for i in range(num,0,-1):
            M.WriteInt(i)
            time.sleep(0.01)
    except KeyboardInterrupt:
        print(" Interrupted")
    except Exception as e:
        print("Error")
        print(e)

if __name__ == '__main__':
    import sys
    main(sys.argv)
