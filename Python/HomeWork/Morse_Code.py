import time
import RPi.GPIO as GPIO # This is commented out, since the notebook is not on the RPi.

LED = 16  # The LED is on pin 16
#
# Initalize the GPIO system. See Lab 2. (https://learn.sparkfun.com/tutorials/raspberry-gpio/python-rpigpio-api)
#
# Un-comment on the RPi
GPIO.setmode(GPIO.BCM)
GPIO.setup(LED, GPIO.OUT)
GPIO.output(LED, GPIO.LOW)
#
Morse_Code={'A':'.-',   'B':'-...', 'C':'-.-.', 'D':'-..',   'E':'.',     'F':'..-.',
            'G': '--.', 'H':'....', 'I':'..',   'J':'.---',  'K':'-.-',   'L':'.-..',
            'M':'--',   'N':'-.',   'O':'---',  'P': '.--.', 'Q': '--.-', 'R': '.-.',
            'S': '...', 'T': '-',   'U':'..-', 'V': '...-','W': '.--',   'X': '-..-',
            'Y': '-.--','Z': '--..',' ':'  ',
            '0': '-----',  '1': '.----',  '2': '..---',
            '3': '...--',  '4': '....-',  '5': '.....',
            '6': '-....',  '7': '--...',  '8': '---..',
            '9': '----.' }
# Ask the user for an input string, then print that string back all capital and in Morse Code

answer = input("Please input your string:")
print("Converted to upper case: ",answer.upper())
#
# Method 1 to convert the letters to Morse code, using a loop.
#
ans_morse = []   # Prepare an empty string
for ch in answer.upper():
    ans_morse.append(Morse_Code[ch])
#
# Method 2 to convert letters to Morse Code, using "list comprehension"
# This is more efficient than using a loop.
#
ans_morse = [ Morse_Code[ch] for ch in answer.upper()]
#
# Convert individual letters in a list to a string. We want a space
# between the letters. To do this we use the .join() method of strings.
#
ans_morse_str=' '.join(ans_morse)
#
# Print the output to the screen.
#
print("In Morse Code:",ans_morse_str)
#
# Now go over the Morse Code string and convert it into pulses.
#
time_unit= 0.1 # This determines the speed. A . is one unit, a - is three units.
for ch in ans_morse_str:
    if ch == ".": # LED on for 1 unit, off for one unit
        print(". = LED on for 1 unit, off for one unit.")
        GPIO.output(LED, GPIO.HIGH)
        time.sleep(time_unit)
        GPIO.output(LED, GPIO.LOW)
        time.sleep(time_unit)
    elif ch == "-": # LED on for 3 units, off for one unit
        print("- = LED on for 3 units, off for one unit.")
        GPIO.output(LED, GPIO.HIGH)
        time.sleep(3*time_unit)
        GPIO.output(LED, GPIO.LOW)
        time.sleep(time_unit)
    elif ch == " ": # LED off for extra unit.
        # LED should be off already
        print("  = LED off for additional unit")
        time.sleep(time_unit)
    else:
        print("There is an invalid character in the string.")

print("We are done.")
