#!/usr/bin/env python
#
# This is a test code is intended to readout a set of 3 SN74HC165 chips
# connected to two SN74HC4040 counters, for a 24-bit serial readout counter.
# The counter input should be gated using a NAND gate to a GPIO pin.
#
# Author: Maurik Holtrop
#
# Basic operation:
#  1) Setup the GPIO input and output ports.
#  2) Send a counter clear signal on the Counter_Clear pin.
#  3) Open the AND (or NAND) gate to the counter clock. (See notes)
#  4) Wait, or run code to be timed.
#  5) Close the AND gate.
#  6) Send a Load signal to the SN74HC165 chip on Serial_Load.
#  7) Readout the SN74HC165 for Serial_N clocks on Serial_CLK by loading the
#     bits from the Serial_In.
#  8) Print the resulting number to the screen.
#
# Notes:
#     * When using the SN74HC193 chip for counting, you can gate by
#       sending the Counter_Gate signal to the "down" clock, and the Clock
#       to be counted to the "up" clock.
#     * When using the SN74HC4040 chip, add a NAND gate to the CLK input.
#       One input of the NAND gate goes to the Counter_Gate, the another
#       to the clock to be counted.
#
#
import RPi.GPIO as GPIO
from DevLib import SN74HC165,MAX7219
import time
import datetime
from dateutil import parser as datparse
import sys
import math
import csv

Counter_Clear = 17
Counter_Gate = 16


Serial_In  = 18   # GPIO pin for the SER pin of the shifter
Serial_CLK = 19   # GPIO pin for the CLK pin of the shifter
Serial_Load= 20   # GPIO pin for the SH/LD-bar pin of the shifter
Serial_N   = 32   # Number of bits to shift in. 8 bits for every SN74HC165

Max_data = 0        # Use 0 for SPI connection, otherwise use GPIO pin connected to driving
Max_clock= 1000000  # Use clock frequency for SPI connection, otherwise use GPIO pin connected to CLK
Max_cs_bar = 0      # Use channel (CE0 or CE1) for SPI connection, otherwise use GPIO pin for CS

S = None  # Placeholder, make sure you run Setup() before using.
M = None


def Setup():
    '''Set the RPi to read the shifterers and communucate with the MAX7219 '''
    global S
    global M

    GPIO.setmode(GPIO.BCM)  # Set the numbering scheme to correspond to numbers on Pi Wedge.

    S = SN74HC165(Serial_In,Serial_CLK,Serial_Load,Serial_N) # Initialize serial shifter.
    M = MAX7219(Max_data,Max_clock,Max_cs_bar)               # Initialize the display.
    M.SetBrightness(2)

    GPIO.setup(Counter_Clear,GPIO.OUT)
    GPIO.setup(Counter_Gate,GPIO.OUT)
    GPIO.output(Counter_Gate,0)
    ClearCounter()

def ClearCounter():
    '''Clear the counter by pulsing the Counter_Clear pin high'''
    GPIO.output(Counter_Clear,1)
    GPIO.output(Counter_Clear,0)

def Cleanup():
    GPIO.cleanup()

def LoadAndShift():
    ''' Load a number into the shifters and then read it out.'''
    S.Load_Shifter()
    return(S.Read_Data())

def Main():
    ''' Run a basic counter code. '''
    Setup()
    time_now=time.time()
    print("Starting Calibration at {}".format(time.ctime(time_now)))
    sys.stdout.flush()

# To store the data in a csv file.
    fout=open("counter_dat.csv","w")
    wr = csv.writer(fout)
    df_cols=["idx","count","dtime","freq","freq_now","freq_now_ave","freq_now_sigma"]
    wr.writerow(df_cols)
    ClearCounter()
    itt=0
    freq_now_sum=0
    freq_now_ssq=0

    time_start=time.time()
    GPIO.output(Counter_Gate,1)  # Start the counter
    last_count=0
    last_now=time_start
    try:
        while time_now < time_start+3600*12:  # Run for 12 hours
            itt+=1
            time.sleep(0.9976)              # Sleep for not quite 1 second while the counter counts.
            count = LoadAndShift()
            now= time.time()
            diff_count=count-last_count
            diff_time=now-last_now
            last_count=count
            last_now=now
            dt=now-time_start
            freq=count/dt
            freq_now=diff_count/diff_time
            freq_now_sum += freq_now
            freq_now_ssq += freq_now*freq_now
            freq_now_ave = freq_now_sum/itt
            freq_now_sigma= math.sqrt(freq_now_ssq/itt - freq_now_ave*freq_now_ave)
            M.WriteFloat(freq)
            print("{:14d} ({:9d}), {:12.4f} ({:4.3f}), {:16.8f}, {:16.8f}, {:16.8f}+/-{:12.8f} ".format(count,diff_count,dt,diff_time,freq,freq_now,freq_now_ave,freq_now_sigma)) # Print the itteration and the counts.
            sys.stdout.flush()
            wr.writerow([itt,count,dt,freq,freq_now,freq_now_ave,freq_now_sigma])
    except KeyboardInterrupt:
        print("Interrupted.")
    except Exception as e:
        print("Error")
        print(e)
    fout.close()
    Cleanup()


if __name__ == "__main__":
    Main()
    sys.exit()
