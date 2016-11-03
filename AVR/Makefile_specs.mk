################################################
#
# Makefile Specifications Template for Arduino code
# Author: Maurik Holtrop
# Copyleft.
#
# Version 2
#
################################################
#
# Note:
# This file follows the GNU Makefile conventions.
# Everything after the "#" symbol is a comment.
# Variables are defined with: NAME=Value.
# For full details on Makefile see: https://www.gnu.org/software/make/manual/make.html
#
#
# Type of board, for the pin layout library.
# You find the possible board definitions in ../include/variants
# For an actual Arduino, this would be "standard" or "leonardo", or "mega".
# For Phys605 we use a bare chip, for which we made a custom pinout: atmega328p
# The atmega168, atmega168p, atmega328, atmega328p all have the same layout.
BOARD_TYPE=atmega328p

# The type of the chip as the avr-gcc compiler expects it.
# You can find the types of chips supported with "avr-gcc -dumpspecs | grep mmcu="
# The value is passed to the compiler as: avr-gcc -mmcu=$(MCU)
# Here it is important to specify the actual number on the chip you are using.
# For Phys605, this will be the atmega328p
#
# Other Examples: atmega168p  atmega328p  atmega168, atmega168p
MCU=atmega168

# Frequency of CPU.
# This depends on how you wired up your circuit.
# The number is rounded to the nearest MHz, but is specified in Hz
# The value is passed to the code through a #define from the commandline:
# avr-gcc ... -DF_CPU=$(F_CPU)
# It depenends on the code to use this correctly. It is important for all those
# pieces of code that critically depend on timing, such as Serial and Wire.
#
# Without a crystal, this is 1 MHz standard (1000000), or 8 MHz (8000000) with a fuse setting.
# With a crystal, it is probably either 16 MHz or 20 MHz.
#F_CPU=16000000
F_CPU=20000000
#F_CPU=1000000
#F_CPU=8000000
#
# The system type controls where the library is installed. 
# This is useful if you are working with different chips.
# Make sure that your program is linked with the correct library for your chip.
# We set this automatically from the MCU and F_CPU choices above. 
SYSTEM_TYPE=$(MCU)_$(F_CPU)

# Chip id to use with programmer
#
# This id specifies the chip you use. For many chips
# it will accept the same name as the one used for the
# MCU. The chip will often also have a shorthand name. 
# You can find a list of supported chip names by
# executing: avrdude -c avrisp2 -p type
#
# For Phys605, the default works.
#
PROGRAMMER_MCU=$(MCU)

# Programmer to use.
#
# There are many different ways to program the ATMega chips,
# and so there are a lot of different programmers available.
# For Phys605 we are using the RaspberryPi through the 
# linuxgpio driver. This custom programmer is defined in the
# file ~/.avrduderc.
# We chose there to use the pins of the Pi as follows:
#
AVRDUDE_PROGRAMMERID=RaspberryPi

# If you are using a programmer like the AVRISP from your
# laptop or desktop computer, or if you are using an actual
# Arduino, you need to specify additional parameters, such
# as the port on your computer that is being used, and the
# speed at which this port runs.
# We don't need this for our linuxgpio setup in Phys605
#
#AVRDUDE_PORT=/dev/tty.usbserial-A9005cJ0
#AVRDUDE_PORT=/dev/tty.usbserial-A6008hex
#AVRDUDE_EXTRA_FLAGS= -F -b57600 -V
#AVRDUDE_PORT=usb


