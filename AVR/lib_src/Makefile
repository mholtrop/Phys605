#############################################
#  
#   Mother Makefile
#
#  Calls the other makefiles to build the libraries.
#
#############################################

AVR_HOME ?= ${HOME}/code/AVR

UTILS= Adafruit_NeoPixel EEPROM Firmata LiquidCrystal SPI Sensirion  SoftwareSerial Wire RF24
CORE = Core


all: includes libarduino.a  libardionoutil.a


includes:
	@echo "Installing all includes"
	@for i in $(CORE) $(UTILS); do \
	    cd $$i; make includes; cd ..;\
	done

libarduino.a:
	@for i in $(CORE); do \
	   echo  "\nMaking $$i \n"; cd $$i; make all; cd ..; \
	done

libardionoutil.a:
	@for i in $(UTILS); do \
	    echo  "\nMaking $$i \n"; cd $$i; make all;  cd ..; \
	done


install:
	@for i in $(CORE) $(UTILS); do \
	    cd $$i; make install;  cd ..; \
	done


clean:
	@for i in $(CORE) $(UTILS); do \
	    echo "Cleaning $$i  "; cd $$i; make clean;  cd ..; \
	done

distclean:
	@for i in $(CORE) $(UTILS); do \
	    echo "DistCleaning $$i  "; cd $$i; make distclean;  cd ..; \
	done

help:
	@cd Core; make help; cd ..
