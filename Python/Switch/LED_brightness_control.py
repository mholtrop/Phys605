#!/usr/bin/env python3
#
# Use two buttons on BCM GPIO pins 16 and 12 to make an LED go brigher or dimmer
# respectively. The LED is hooked up on GPIO18, which can do PWM.
# Hook up the LED with a transistor so that full brightness is actually bright.
# For 3.3V and a RED LED, a 50 Ohm resistor and a 2N3904 transistor work well.
#
import RPi.GPIO as GPIO
import time 
#
GPIO.setmode(GPIO.BCM)
print("Start of program")
GPIO.setup(16, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(12, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(18, GPIO.OUT)
pwm  = GPIO.PWM(18, 100)     # Setup the PWM at 100 Hz frequency.
                             # For high frequencies the dimming does not work so well.
value=20                     
pwm.start(value)                # Start at low brightness


while(True):   # Still an infinite loop
    if(GPIO.input(16)): # So the button was pushed down the first time.
        value+= 5
        if value>100:
            value=100
        time.sleep(0.001)          # Wait for any bouncing to die out.
        while( GPIO.input(16) ):  # If the button is still down
                 time.sleep(0.001)    # Wait some more
        print("V = {}".format(value))
    if(GPIO.input(12)): # So the button was pushed down the first time.
        value+= -5
        if value<0:
            value=0
        time.sleep(0.005)          # Wait for any bouncing to die out.
        while( GPIO.input(12) ):  # If the button is still down
                 time.sleep(0.005)    # Wait some more

        print("V = {}".format(value))
    pwm.ChangeDutyCycle(value)    # Update he PWM duty cycle all the time.
