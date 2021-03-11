#!/usr/bin/env python3
#
# Use two buttons on BCM GPIO pins 16 and 12 to make an LED go brigher or dimmer
# respectively. The LED is hooked up on GPIO18, which can do PWM.
# Hook up the LED with a transistor so that full brightness is actually bright.
# For 3.3V and a RED LED, a 50 Ohm resistor and a 2N3904 transistor work well.
#
import time

try:
    import RPi.GPIO as GPIO
except ImportError as e:
    print("Could not import GPIO module, so probably not running on the RPi.")
#
GPIO.setmode(GPIO.BCM)

LED_Pin = 17

print("Start of program")
print("Press control-C to stop.")
GPIO.setup(LED_Pin, GPIO.OUT)

while(True):   # Still an infinite loop. End the loop by pressing control-C at the terminal.
    GPIO.output(LED_Pin, 0)
    print("off")
    time.sleep(1)
    GPIO.output(LED_Pin, 1)
    print("on")
    time.sleep(1)

