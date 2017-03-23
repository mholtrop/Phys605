#!/usr/bin/env python

import RPi.GPIO as GPIO
import time
import sys


OUT_CLK     = 23
OUT_DATA    = 24
OUT_CS_bar  = 25

Serial_In  = 18   # GPIO pin for the SER pin of the shifter
Serial_CLK = 19   # GPIO pin for the CLK pin of the shifter
Serial_Load= 20   # GPIO pin for the SH/LD-bar pin of the shifter
Serial_N   = 24   # Number of bits to shift in. 8 bits for every SN74HC165

def Setup():
    '''Set the RPi to read the shifterers and communucate with the MAX7219 '''
    GPIO.setmode(GPIO.BCM)  # Set the numbering scheme to correspond to numbers on Pi Wedge.

    GPIO.setup(Serial_CLK,GPIO.OUT)
    GPIO.setup(Serial_In,GPIO.IN)
    GPIO.setup(Serial_Load,GPIO.OUT)
    GPIO.output(Serial_CLK,0)
    GPIO.output(Serial_Load,1)

    # Initialize the MAX7219 output display
    GPIO.setup(OUT_CLK,GPIO.OUT)  
    GPIO.setup(OUT_DATA,GPIO.OUT)
    GPIO.setup(OUT_CS_bar,GPIO.OUT)
    GPIO.output(OUT_CLK,0)
    GPIO.output(OUT_DATA,0)
    GPIO.output(OUT_CS_bar,1)



    
def WriteData(data):
    '''Write the 16 bit data to the output '''
    GPIO.output(OUT_CS_bar,0)
    
    for i in range(16):  # send out 16 bits.
        GPIO.output(OUT_CLK,0)
        #time.sleep(0.00001)
        bit = data & 0x8000
        GPIO.output(OUT_DATA,bit)
        #time.sleep(0.00001)
        GPIO.output(OUT_CLK,1)
        #time.sleep(0.00001)
        data <<=1
        if(i==7):
            GPIO.output(OUT_CLK,0)
            GPIO.output(OUT_DATA,0)
        #    time.sleep(0.00003)
            
    GPIO.output(OUT_DATA,0)
    GPIO.output(OUT_CLK,0)
    GPIO.output(OUT_CS_bar,1)
       
def WriteChar(loc,dat):
    '''Write dat to loc. If the mode is 1 then dat is a number and loc is the location.
       If mode is 2 then dat is an 8 bit LED position.'''
    
    out = (loc <<8)
    out += dat
    #out += 0b0000000000000000  # Dummy bits

    WriteData(out)

def Init(mode):
    ''' Initialize the MAX7219 Chip. Mode=1 is for numbers, mode=2 is no-decode'''
    WriteChar(0x0C,1) # Set for normal operation.
    if mode == 1:
        WriteChar(0x09,0xFF)
    else:
        WriteChar(0x09,0x00)
            
def Cleanup():
    WriteChar(0x0C,0x0) # Turn off
    GPIO.cleanup()


def WriteInt(n):
    ''' Write the integer n on the display '''
    if n > 99999999:
        for i in range(8):
            WriteChar(i+1,0x0A)
        return
    
    for i in range(8):
        n,d = divmod(n,10)
        if n==0 and d == 0:
            WriteChar(i+1,0x0F) # Blank
        else:
            WriteChar(i+1,d)

def LoadAndShift(Nbits=Serial_N):
    ''' Load a numner into the N shifters and then read it out by shifting.'''
    GPIO.output(Serial_Load,0) # load data
    GPIO.output(Serial_Load,1) # Ready to shift in.

    out=0
    for i in range(Serial_N):
        bit = GPIO.input(Serial_In)    # First bit is already present on SER after load.        
        out <<= 1                      # Shift the out bits one to the left.
        out += bit                     # Add the bit we just read.
        GPIO.output(Serial_CLK, GPIO.HIGH) # Clock High loads next bit
        GPIO.output(Serial_CLK, GPIO.LOW)  # Clock Low resets cycle.
    return(out)

def Main():
    ''' Run a basic counter code. '''
    print "send on"
    Setup()
    Init(1)
    print "counting"
    i=0
    while i < 100000000:
        i+=1
        WriteInt(i*10)

    Cleanup()

            
if __name__ == "__main__":
    Main()
    sys.exit()
