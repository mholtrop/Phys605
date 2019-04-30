#!/usr/bin/env python
#
# Despite the name, this driver should work with:
# MPC424x,MCP425x,MCP426x,MCP414x,MCP415x,MCP416x
# where x is 1 or 2
#
# Tested with MCP4251 and MPC4161
#
# Author: Maurik Holtrop
#
# This  module interfaces with an MCP4251 or MCP4161 digital programmable resistor.
# See the datasheet for details.
#
# For the 4161, since the SDI/SDO are a single pin, the big bang interfaces
# uses a one data wire protocol, so no resistors are needed. On the SpiDev you will
# need a 1kOhm to 10kOhm resistor from the Raspberry Pi MOSI to MISO pin. Note that
# this resistor can interfere with other devices on the bus, so bit bang may be preferred.
#
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
# If the device is connected to the hardware SPI:
# The MCP42xx devices have separate SDO and SDI pins, and can communicate at the full 10MHz SPI clock.
# For the MCP41x1 devices, you have a SDI/SDO combined pin. This pin is connected directly
# to the MISO pin, and with a resistor to the MOSI pin on the RaspberryPi.
# With a 10kOhm resistor I could get reliable data transfer at 250kHz clock speed, but not at 500kHz.
# With a 1kOhm resistor, I could write at 5 MHz, but not at 10 MHz. Specifications state that
# reading should not be more than 250kHz in these cases, but I found 5 MHz worked.
#
# To accomodate high speed writing for the MCP41x1 devices, the clock speed is adjusted for These
# chips when using hardware SPI
#
# Note for Bit Bang: On a standard Raspberry Pi 3, the maximum bit-bang frequency that I measured
# with the current version of this code, using ipython3, was about 85 kHz for one of the pulses of the clock.
# Since there is nothing in this code limiting the bit-bang speed, a faster RPi, or faster version of
# Python, may exceed the 250kHz maximum speed of the MCP4161.
#
try:
    import RPi.GPIO as GPIO
except:
    try:
        import Adafruit_BBIO as GPIO
    except:
        raise("Could not find a GPIO library")

import spidev

class MCP4251(object):

    def __init__(self,CS_bar_pin,CLK_pin=10000000,MOSI_pin=0,MISO_pin=0,chip=None):
        '''Initialize the code and set the GPIO pins.
        If MOSI_pin = 0, the code assumes hardware SPI mode, in which case the
        CLK_pin number is taken as the maximum clock speed desired. This clock speed
        is adjusted for the MCP41x1 devices which have a combined SDI/SDO pin.
        If MOSI_pin !=0, then bit bang mode is used and all the GPIO pin numbers
        must be specified. For MCP41x1 devices, specify MISO_pin=MOSI_pin.'''

        self.CLK = CLK_pin
        self.MOSI = MOSI_pin
        self.MISO = MISO_pin
        self.CS_bar = CS_bar_pin

        self._CMDERR_bit=0b00000010  # Seventh bit send out is the ERROR bit.
        # Dictionary: chip_name: (channels, readspeed, writespeed,steps,I/O type)
        # I/O type can be 0 for 2 channel SPI or 1 for SDO/SDI combined.
        # This is only relevant when you use the BITBANG SPI mode.
        #
        chip_dict={
            'MCP4251':(2,10000000,10000000,256,0),
            'MCP4161':(1,250000,5000000,256,1)}

        if chip in chip_dict:
            self._chip = chip_dict[chip]
            self.Nchannels    =  self._chip[0]
            self.MaxReadSpeed =min(self._chip[1],CLK_pin)
            self.MaxWriteSpeed=min(self._chip[2],CLK_pin)
        else:
            print("Chip not specified or not known yet, please add to dictionary:",chip)
            raise("Chip not OK error")

        if self.MOSI > 0:  # Bing Bang mode
            assert self.MISO !=0 and self.CLK < 32
            if self._chip[4] == 1:
                 assert self.MOSI == self.MISO
            if GPIO.getmode() != 11:
                GPIO.setmode(GPIO.BCM)        # Use the BCM numbering scheme

            GPIO.setup(self.CLK,GPIO.OUT)     # Setup the ports for in and output
            if self.Nchannels == 1:
                GPIO.setup(self.MOSI,GPIO.IN)
                assert self.MISO == self.MOSI
                self.Direction = 0
            else:
                GPIO.setup(self.MOSI,GPIO.OUT)
                GPIO.setup(self.MISO,GPIO.IN)
                GPIO.output(self.MOSI,0)          # Set the Master Out low

            GPIO.setup(self.CS_bar,GPIO.OUT)
            GPIO.output(self.CLK,0)           # Set the clock low.
            GPIO.output(self.CS_bar,1)        # Set the CS_bar high

        else:
            self._dev = spidev.SpiDev(0,self.CS_bar)     # Start a SpiDev device
            self._dev.mode = 0                           # Set SPI mode (phase)
            self._dev.max_speed_hz = self.MaxWriteSpeed  # Set the data rate
            self._dev.bits_per_word = 8                  # Number of bit per word. ALWAYS 8

    def __del__(self):
        ''' Cleanup the GPIO before being destroyed '''
        if(self.MOSI>0):
            GPIO.cleanup(self.CS_bar)
            GPIO.cleanup(self.CLK)
            GPIO.cleanup(self.MOSI)
            if self.Nchannels > 1:
                GPIO.cleanup(self.MISO)

    def _SendBits(self,bits,num):
        ''' Send out a stream of bits, MSB first, on GPIO'''
        if self.MOSI == 0:
            return
        #
        # The input is read on the rising edge of the clock.
        #
        if self.Nchannels == 1 and self.Direction == 0:
            GPIO.setup(self.MOSI,GPIO.OUT)
            self.Direction = 1

        for i in range(num-1,-1,-1):
            bit = (bits>>i)&0b1
            GPIO.output(self.CLK,0)    # Return clock to zero.
            GPIO.output(self.MOSI,bit) # Set the bit.
            GPIO.output(self.CLK,1)    # Rising edge sends data
        GPIO.output(self.CLK,0)    # Return clock to zero.



    def _ReadBits(self,num):
        ''' Read a single bit from the ADC and pulse clock.'''
        if self.MOSI == 0:
            return 0

        if self.Nchannels == 1 and self.Direction == 1:
            GPIO.setup(self.MOSI,GPIO.IN)
            self.Direction = 0

        out=0
        for i in range(num):
            out <<= 1               # Shift all the bits left.
            GPIO.output(self.CLK,1) # Set the clock high. Ready to read.
            bit = GPIO.input(self.MISO) # Read the next bit.
            GPIO.output(self.CLK,0) # Return clock low, next bit will be set.
            out+=bit                # Add bit to the output.

        return(out)

    def _WriteWords(self,data):
        '''Write the data in "data" to the device, and return the answer.
        Data is a list of 8-bit words to be written. The same number of words is returned.
        Note that bit-banged single pin operation is treaded seprately.'''

        if self.MOSI == 0:
            answer=self._dev.xfer2(data)
        else:                          #### BIT BANG CODE
            GPIO.output(self.CLK,0)      # Make sure clock starts low.
            if self.Nchannels == 1:
                GPIO.setup(self.MOSI,GPIO.OUT) # Turn on the output.
            GPIO.output(self.MOSI,0)
            GPIO.output(self.CS_bar,0)   # Start sequence
            ans=0
            answer=[]
            #
            # Every sequence starts with a 4 bit ADDRESS
            # followed by a 2 bit "command":
            #   00  = write command
            #   11  = read command
            #   01  = Increment
            #   10  = Decrement
            #
            # Next is acknowledge bit, which is a read.
            # This is then follow by bit8 of the write, or read, or a dummy.
            # For write or read the next 8 bits are data.
            #
            l=0
            while l < len(data):
                d = data[l]
                address = (d>>4)
                command = ((d & 0b1100)>>2)
                highbit = d&0b01
                self._SendBits(address,4) # Send the 4 address bits.
                self._SendBits(command,2) # Send the 2 command bits.
                ack_bit=self._ReadBits(1) # Read the acknowledge bit.
                if command == 0b00:      # Write operation
                    self._SendBits(highbit,1)
                    self._SendBits(data[l+1],8)
                    l += 1
                    answer.append( (ack_bit<<1))
                    answer.append(0)
                elif command == 0b11:      # Read Operation.
                    ans = self._ReadBits(1) # Read the high bit.
                    ans += (ack_bit<<1)
                    answer.append(ans)
                    ans = self._ReadBits(8) # Read the answer
                    answer.append(ans)
                    l += 1                 # Skip the dummy word.
                else:
                    ans = self._ReadBits(1) # Read the high bit.
                    ans += (ack_bit<<1)
                    answer.append(ans)     # There is no dummy word!

                l += 1

            GPIO.output(self.CS_bar,1)  # Deselect the chip.
            GPIO.output(self.CLK,0)     # End, make sure clock is low.
            if self.Nchannels==1:
                if self.Direction == 0:
                    GPIO.setup(self.MOSI,GPIO.OUT) # Turn on the output.
                    self.Direction == 1

            GPIO.output(self.MOSI,0)    # and MOSI is low.
        return(answer)  # Return answer

    def _ReadAddress(self,addr):
        '''Read an address from the chip and return it.
        Returns None if the read had an error.'''
        low_word=0xFF                               # The read part must be high for the 4161 chips.
        command = ((addr&0x0F)<<4) + 0b1111     # Address (4bits), read command, 11
        if self.MOSI==0:                        # Set slower read on spidev.
            self._dev.max_speed_hz=self.MaxReadSpeed

        ans=self._WriteWords([command,low_word])

        if self.MOSI==0:                        # Restore to write speed on spidev.
            self._dev.max_speed_hz=self.MaxWriteSpeed

        if( (ans[0]&self._CMDERR_bit)>0):
            return(ans[1]+ ( (ans[0]&0b01)<<8) )
        else:
            return(None)                    # Error

    def _WriteAddress(self,addr,data):
        '''Write data to addr on the chip.'''
        low_word= data&0xFF                  # Low 8 bits of data
        command = ((addr&0x0F)<<4) + 0b0010 + ((data&0x100)>>8)   # Address (4bits), write (00), 1, highbit
        ans=self._WriteWords([command,low_word])
        if( (ans[0]&self._CMDERR_bit)>0):
            return(ans[1]+ ( (ans[0]&0b01)<<8) )
        else:
            return(None)                    # Error


    def SetWiper(self,setpoint=128,wiper=0):
        '''Set the wiper to setpoint. Setpoint can be between 0 and MAX inclusive,
        where MAX is 256 for the MCP4251
        Returns True if status is OK'''
        assert 0<= wiper < self._chip[0]
        assert 0<= setpoint <= self.GetWiperMax()
        addr = wiper&0b01 # Address (0 or 1) and command (00) and hi bit
        ans=self._WriteAddress(addr,setpoint) # Send/receive data.
        return(ans)    # Return True if status OK

    def ReadWiper(self,wiper=0):
        '''Read the wiper value from the chip and return it.
        Returns None if the read had an error.'''
        assert 0<= wiper < self._chip[0]
        addr = wiper&0b01
        ans=self._ReadAddress(addr)
        return(ans)

    @property
    def wiper(self):
        """The wiper of the variable resistor"""
        return(self.ReadWiper(0))

    @wiper.setter
    def wiper(self,value):
        return(self.SetWiper(value,0))

    @property
    def wiper2(self):
        """The wiper of the variable resistor"""
        return(self.ReadWiper(1))

    @wiper2.setter
    def wiper2(self,value):
        return(self.SetWiper(value,1))

    def GetWiperMax(self):
        """Return the maximum possible value for wiper. """
        return(self._chip[3])

    def IncrementWiper(self,wiper=0):
        '''Increment the wiper by one setting. Returns True is successful'''
        assert 0<= wiper < self._chip[0]
        command = ((wiper&0b01)<<4) + 0b0111   # Address (0 or 1) and INCR command.
        ans=self._WriteWords([command])
        return((ans[0]&self._CMDERR_bit)>0)

    def DecrementWiper(self,wiper=0):
        '''Decrement the wiper by one setting. Returns True is successful'''
        assert 0<= wiper < self._chip[0]
        command = ((wiper&0b01)<<4) + 0b1011   # Address (0 or 1) and DECR command.
        ans=self._WriteWords([command])
        return((ans[0]&self._CMDERR_bit)>0)

    def Reset(self):
        '''Reset the chip:
        Connect the wipers and A,B contacts and set them in the middle.'''
        self.SetWiper(self.GetWiperMax()//2,0)
        if self.Nchannels == 2:
            self.SetWiper(self.GetWiperMax()//2,1)
        self._WriteWords([0b01000001,0xFF])        # Write the TCON to all connected, no shutdown.

    def DisconnectWiper(self,wiper=0):
        '''Disconnect the W terminal from the wiper'''
        assert 0<= wiper < self._chip[0]
        stat,tcon = self._WriteWords([0b01001100,0]) # Read address=4
        if(wiper==0):
            tcon = tcon & 0b11111101
        else:
            tcon = tcon & 0b11011111
        ans = self._WriteWords([0b01000001,tcon])
        return((ans[0]&self._CMDERR_bit)>0)

    def ConnectWiper(self,wiper=0):
        '''Connect the W terminal from the wiper'''
        assert 0<= wiper < self._chip[0]
        stat,tcon = self._WriteWords([0b01001100,0]) # Read address=4
        if(wiper==0):
            tcon = tcon | 0b00000010
        else:
            tcon = tcon | 0b00100000
        ans = self._WriteWords([0b01000001,tcon])
        return((ans[0]&self._CMDERR_bit)>0)

    def DisconnectA(self,wiper=0):
        '''Disconnect the A terminal from the array'''
        assert 0<= wiper < self._chip[0]
        stat,tcon = self._WriteWords([0b01001100,0]) # Read address=4
        if(wiper==0):
            tcon = tcon & 0b11111011
        else:
            tcon = tcon & 0b10111111
        ans = self._WriteWords([0b01000001,tcon])
        return((ans[0]&self._CMDERR_bit)>0)

    def ConnectA(self,wiper=0):
        '''Connect the A terminal from the array'''
        assert 0<= wiper < self._chip[0]
        stat,tcon = self._WriteWords([0b01001100,0]) # Read address=4
        if(wiper==0):
            tcon = tcon | 0b00000100
        else:
            tcon = tcon | 0b01000000
        ans = self._WriteWords([0b01000001,tcon])
        return((ans[0]&self._CMDERR_bit)>0)

    def DisconnectB(self,wiper=0):
        '''Disconnect the B terminal from the array'''
        assert 0<= wiper < self._chip[0]
        stat,tcon = self._WriteWords([0b01001100,0]) # Read address=4
        if(wiper==0):
            tcon = tcon & 0b11111110
        else:
            tcon = tcon & 0b11101111
        ans = self._WriteWords([0b01000001,tcon])
        return((ans[0]&self._CMDERR_bit)>0)

    def ConnectB(self,wiper=0):
        '''Connect the B terminal from the array'''
        assert 0<= wiper < self._chip[0]
        stat,tcon = self._WriteWords([0b01001100,0]) # Read address=4
        if(wiper==0):
            tcon = tcon | 0b00000001
        else:
            tcon = tcon | 0b00010000
        ans = self._WriteWords([0b01000001,tcon])
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

    print("We assume that you are using an MCP4251 chip!")
    P = MCP4251(cs_bar,clk_pin,mosi_pin,miso_pin,chip="MCP4251")
    try:
        P.SetWiper(0,0)
        wiper=0
        for i in range(P.GetWiperMax()/8):
            P.SetWiper(wiper,0)
            value = 3.3*wiper/float(P.GetWiperMax())
            print("Volt meter should read {:6.3f}".format(value))
            wiper += 8
            time.sleep(1)
        for i in range(P.GetWiperMax()):
            P.DecrementWiper(0)
            wiper=P.ReadWiper(0)
            value = 3.3*wiper/float(P.GetWiperMax())
            print("Volt meter should read {:6.3f}".format(value))
            time.sleep(1)

    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == '__main__':
    import sys
    import time

    main(sys.argv)
