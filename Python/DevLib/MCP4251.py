#!/usr/bin/env python
#
# MCP320x
#
# Author: Maurik Holtrop
#
# This  module interfaces with an MCP4251 digital programmable resistorself.
# See the datasheet for details.

# SPI Modes:
# MODE 0,0
# In Mode 0,0: SCK idle state = low (VIL), data is clocked in on the SDI pin on
# the rising edge of SCK and clocked out on the SDO pin on the falling edge of SCK.
# MODE 1,1
# In Mode 1,1: SCK idle state = high (VIH), data is clocked in on the SDI pin on
# the rising edge of SCK and clocked out on the SDO pin on the falling edge of SCK.
#
# This driver only supports the 0,0 mode.
#



import RPi.GPIO as GPIO
import spidev

class MCP4251:

    def __init__(self,CS_bar_pin,CLK_pin=1000000,MOSI_pin=0,MISO_pin=0):
        '''Initialize the code and set the GPIO pins.'''

        self.CLK = CLK_pin
        self.MOSI = MOSI_pin
        self.MISO = MISO_pin
        self.CS_bar = CS_bar_pin

        self._CMDERR_bit=0b00000010  # Seventh bit send out is the ERROR bit.


        if self.MOSI > 0:  # Bing Bang mode
            assert self.MISO !=0 and self.CLK < 32
            if GPIO.getmode() != 11:
                GPIO.setmode(GPIO.BCM)        # Use the BCM numbering scheme

            GPIO.setup(self.CLK,GPIO.OUT)     # Setup the ports for in and output
            GPIO.setup(self.MOSI,GPIO.OUT)
            GPIO.setup(self.MISO,GPIO.IN)
            GPIO.setup(self.CS_bar,GPIO.OUT)

            GPIO.output(self.CLK,0)           # Set the clock low.
            GPIO.output(self.MOSI,0)          # Set the Master Out low
            GPIO.output(self.CS_bar,1)        # Set the CS_bar high

        else:
            self._dev = spidev.SpiDev(0,self.CS_bar) # Start a SpiDev device
            self._dev.mode = 0                    # Set SPI mode (phase)
            self._dev.max_speed_hz = self.CLK     # Set the data rate
            self._dev.bits_per_word = 8           # Number of bit per word. ALWAYS 8

        self.Reset()

    def __del__(self):
        ''' Cleanup the GPIO before being destroyed '''
        if(self.MOSI>0):
            GPIO.cleanup(self.CS_bar)
            GPIO.cleanup(self.CLK)
            GPIO.cleanup(self.MOSI)
            GPIO.cleanup(self.MISO)

    def SendBit(self,bit):
        ''' Send out a single bit, and pulse clock.'''
        if self.MOSI == 0:
            return
        #
        # The input is read on the rising edge of the clock.
        #
        GPIO.output(self.CLK,0)    # Return clock to zero.
        GPIO.output(self.MOSI,bit) # Set the bit.
        rbit = int(GPIO.input(self.MISO)) # Read the return bit.
        GPIO.output(self.CLK,1)    # Rising edge sends data
        return(rbit)

    def ReadBit(self):
        ''' Read a single bit from the ADC and pulse clock.'''
        if self.MOSI == 0:
            return 0
        #
        # The output is going out on the falling edge of the clock,
        # and is to be read on the rising edge of the clock.

        # Clock should be already low, and data should already be set.
        GPIO.output(self.CLK,1) # Set the clock high. Ready to read.
        bit = GPIO.input(self.MISO) # Read the bit.
        GPIO.output(self.CLK,0) # Return clock low, next bit will be set.

        return(bit)

    def WriteWords(self,data):
        '''Write the data in "data" to the device, and return the answer.
        Data is a list of 8-bit words to be written. The same number of words is returned.'''

        if self.MOSI == 0:
            answer=self._dev.xfer2(data)
        else:
            GPIO.output(self.CLK,0)      # Make sure clock starts low.
            GPIO.output(self.MOSI,0)
            GPIO.output(self.CS_bar,0)   # Start sequence
            ans=0
            answer=[]
            for d in data:
                for i in range(8):       # We send out 8 bit words
                    bit= d & 0x80     # The highest bit is send first.
                    rbit=self.SendBit(bit>0) # Write out the high bit
                    d= (d<<1)&0xFF # Shift all the bits one position left and truncate.
                    ans = ans<<1
                    ans+= rbit
                answer.append(ans)
            GPIO.output(self.CLK,0)     # End, make sure clock is low.
            GPIO.output(self.MOSI,0)    # and MOSI is low.
            GPIO.output(self.CS_bar,1)  # Deselect the chip.
        return(answer)  # Return answer


    def SetWiper(self,setpoint=128,wiper=0):
        '''Set the wiper to setpoint. Setpoint can be between 0 and MAX inclusive,
        where MAX is 256 for the MCP4251
        Returns True if status is OK'''
        set_low = (setpoint & 0xFF)             # Lower 8 bits
        command = ((wiper&0b01)<<4) + ((setpoint>>8) & 0b01) # Address (0 or 1) and command (00) and hi bit
        ans=self.WriteWords([command,set_low]) # Send/receive data.
        return( (ans[0]&self._CMDERR_bit)>0 )    # Return True if status OK

    def ReadWiper(self,wiper=0):
        '''Read the wiper value from the chip and return it.
        Returns None if the read had an error.'''
        set_low=0
        command = ((wiper&0b01)<<4) + 0b00001100   # Address (0 or 1) and read command.
        ans=self.WriteWords([command,set_low])
        if( (ans[0]&self._CMDERR_bit)>0):
            return(ans[1]+ ( (ans[0]&0b01)<<8) )
        else:
            return(None)                    # Error

    def IncrementWiper(self,wiper=0):
        '''Increment the wiper by one setting. Returns True is successful'''
        command = ((wiper&0b01)<<4) + 0b0100   # Address (0 or 1) and INCR command.
        ans=self.WriteWords([command])
        return((ans[0]&self._CMDERR_bit)>0)

    def DecrementWiper(self,wiper=0):
        '''Decrement the wiper by one setting. Returns True is successful'''
        command = ((wiper&0b01)<<4) + 0b1000   # Address (0 or 1) and DECR command.
        ans=self.WriteWords([command])
        return((ans[0]&self._CMDERR_bit)>0)

    def Reset(self):
        '''Reset the chip:
        Connect the wipers and A,B contacts and set them in the middle.'''
        self.SetWiper(128,0)
        self.SetWiper(128,1)
        self.WriteWords([0b01000001,0xFF])        # Write the TCON to all connected, no shutdown.

    def DisconnectWiper(self,wiper=0):
        '''Disconnect the W terminal from the wiper'''
        stat,tcon = self.WriteWords([0b01001100,0]) # Read address=4
        if(wiper==0):
            tcon = tcon & 0b11111101
        else:
            tcon = tcon & 0b11011111
        ans = self.WriteWords([0b01000001,tcon])
        return((ans[0]&self._CMDERR_bit)>0)

    def ConnectWiper(self,wiper=0):
        '''Connect the W terminal from the wiper'''
        stat,tcon = self.WriteWords([0b01001100,0]) # Read address=4
        if(wiper==0):
            tcon = tcon | 0b00000010
        else:
            tcon = tcon | 0b00100000
        ans = self.WriteWords([0b01000001,tcon])
        return((ans[0]&self._CMDERR_bit)>0)

    def DisconnectA(self,wiper=0):
        '''Disconnect the A terminal from the array'''
        stat,tcon = self.WriteWords([0b01001100,0]) # Read address=4
        if(wiper==0):
            tcon = tcon & 0b11111011
        else:
            tcon = tcon & 0b10111111
        ans = self.WriteWords([0b01000001,tcon])
        return((ans[0]&self._CMDERR_bit)>0)

    def ConnectA(self,wiper=0):
        '''Connect the A terminal from the array'''
        stat,tcon = self.WriteWords([0b01001100,0]) # Read address=4
        if(wiper==0):
            tcon = tcon | 0b00000100
        else:
            tcon = tcon | 0b01000000
        ans = self.WriteWords([0b01000001,tcon])
        return((ans[0]&self._CMDERR_bit)>0)

    def DisconnectB(self,wiper=0):
        '''Disconnect the A terminal from the array'''
        stat,tcon = self.WriteWords([0b01001100,0]) # Read address=4
        if(wiper==0):
            tcon = tcon & 0b11111110
        else:
            tcon = tcon & 0b11101111
        ans = self.WriteWords([0b01000001,tcon])
        return((ans[0]&self._CMDERR_bit)>0)

    def ConnectB(self,wiper=0):
        '''Connect the A terminal from the array'''
        stat,tcon = self.WriteWords([0b01001100,0]) # Read address=4
        if(wiper==0):
            tcon = tcon | 0b00000001
        else:
            tcon = tcon | 0b00010000
        ans = self.WriteWords([0b01000001,tcon])
        return((ans[0]&self._CMDERR_bit)>0)

def main(argv):
    '''Test code for the MCP4251 driver. This assumes you are using a MCP4251.
    If no arguments are supplied, then use SPIdev for CE0 and read channel 0
    Connect the P0A to 3.3V, the P0B to ground, and the P0W to a volt meter,
    or better the Analog Discovery data logger.'''


    if len(argv) < 2:
        cs_bar=0
        clk_pin=1000000
        mosi_pin=0
        miso_pin=0
        channel =0
    elif len(argv) < 6:
        print("Please supply: cs_bar_pin clk_pin mosi_pin miso_pin channel")
        sys.exit(1)

    else:
        cs_bar  = int(argv[1])
        clk_pin = int(argv[2])
        mosi_pin= int(argv[3])
        miso_pin= int(argv[4])
        channel = int(argv[5])

    P = MCP4251(cs_bar,clk_pin,mosi_pin,miso_pin)
    try:
        P.SetWiper(0,0)
        wiper=0
        for i in range(256/8):
            P.SetWiper(wiper,0)
            value = 3.3*wiper/256.
            print("Volt meter should read {:6.3f}".format(value))
            wiper += 8
            time.sleep(1)
        for i in range(256):
            P.DecrementWiper(0)
            wiper=P.ReadWiper(0)
            value = 3.3*wiper/256.
            print("Volt meter should read {:6.3f}".format(value))
            time.sleep(1)

    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == '__main__':
    import sys
    import time

    main(sys.argv)
