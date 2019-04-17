#############################################
#  
#   Mother Makefile
#
#  Calls the other makefiles to build the libraries.
#
#############################################

AVR_HOME ?= ${HOME}/Phys605/AVR

UTILS= Adafruit_NeoPixel EEPROM Firmata LiquidCrystal SPI Sensirion  SoftwareSerial Wire
# RF24
CORE = Core


all: includes libarduino.a  libardionoutil.a


includes:
	@echo "Installing all includes"
	@for i in $(CORE) $(UTILS); do make -C $$i includes ; done

libarduino.a:
	@for i in $(CORE); do echo  "\nMaking $$i \n"; make -C $$i all; cd ..; done

libardionoutil.a:
	@for i in $(UTILS); do echo  "\nMaking $$i \n"; make -C $$i all; done


install:
	@for i in $(CORE) $(UTILS); do  make -C $$i install; done


clean:
	@for i in $(CORE) $(UTILS); do  echo "Cleaning $$i  "; make -C $$i clean; done

distclean:
	@for i in $(CORE) $(UTILS); do  echo "DistCleaning $$i  "; make -C $$i distclean; done

help:
	@cd Core; make help; cd ..
