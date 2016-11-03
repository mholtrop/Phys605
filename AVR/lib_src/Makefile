#############################################
#  
#   Mother Makefile
#
#  Calls the other makefiles to build the libraries.
#
#############################################

AVR_HOME ?= ${HOME}/code/AVR

UTILS= Adafruit_NeoPixel EEPROM Firmata LiquidCrystal SPI Sensirion  SoftwareSerial Wire
CORE = Core


all: includes libarduino.a  libardionoutil.a


includes:
	for i in $(CORE) $(UTILS); do \
	    echo "Installing includes for $$i";cd $$i; make includes; cd ..;\
	done

libarduino.a:
	for i in $(CORE); do \
	   echo  "Making $$i "; cd $$i; make all; cd ..; \
	done

libardionoutil.a:
	for i in $(UTILS); do \
	    echo "Making $$i  "; cd $$i; make all;  cd ..; \
	done


install:
	for i in $(CORE) $(UTILS); do \
	    echo "installing $$i  "; cd $$i; make install;  cd ..; \
	done


clean:
	for i in $(CORE) $(UTILS); do \
	    echo "Cleaning $$i  "; cd $$i; make clean;  cd ..; \
	done

distclean:
	for i in $(CORE) $(UTILS); do \
	    echo "Cleaning $$i  "; cd $$i; make distclean;  cd ..; \
	done


