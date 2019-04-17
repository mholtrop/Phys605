/*
  pins_arduino.h - Pin definition functions for Arduino
  Part of Arduino - http://www.arduino.cc/

  Copyright (c) 2007 David A. Mellis

  This library is free software; you can redistribute it and/or
  modify it under the terms of the GNU Lesser General Public
  License as published by the Free Software Foundation; either
  version 2.1 of the License, or (at your option) any later version.

  This library is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
  Lesser General Public License for more details.

  You should have received a copy of the GNU Lesser General
  Public License along with this library; if not, write to the
  Free Software Foundation, Inc., 59 Temple Place, Suite 330,
  Boston, MA  02111-1307  USA

  $Id: wiring.h 249 2007-02-03 16:52:51Z mellis $
*/
/* This file was modified from the original "standard" version
   to reflect the pinout of a bare atmega328p chip.
 
   Modified by: Maurik Holtrop
*/

#ifndef Pins_Arduino_h
#define Pins_Arduino_h

#include <avr/pgmspace.h>

#define NUM_DIGITAL_PINS            6
#define NUM_ANALOG_INPUTS           4
#define analogInputToDigitalPin(p)  ((p <= 4) ? (p==1? 0 : (p==2?3:(p==3?2:(p==7:1:-1)))) : -1)
#define digitalPinHasPWM(p)         (-1)

static const uint8_t SS   = -1;
static const uint8_t MOSI = 5;
static const uint8_t MISO = 6;
static const uint8_t SCK  = 7;

static const uint8_t SDA = 5;
static const uint8_t SCL = 7;
#define LED_BUILTIN -1

static const uint8_t A0 = 1;
static const uint8_t A1 = 7;
static const uint8_t A2 = 3;
static const uint8_t A3 = 2;

/* PCICR - input pins. */
#define digitalPinToPCICR(p)    ( (((p) >= 1  ) && ((p) <= 3 )) ||	\
                                  (((p) >= 5 ) && ((p) <= 7)) ?  (&PCICR) : ((uint8_t *)0))
#define digitalPinToPCICRbit(p) (0) /* We only have PORTB */
#define digitalPinToPCMSK(p)    (&PCMSK0) 
#define digitalPinToPCMSKbit(p)  ( ((p)==1)?5 : (((p)==2)?3 : ( ((p)>=5 && (p)<=7 )? ((p)-5) )))  

#define digitalPinToInterrupt(p)  ((p) == 7 ? 0 :  NOT_AN_INTERRUPT )

#ifdef ARDUINO_MAIN

// On the Arduino board, digital pins are also used
// for the analog output (software PWM).  Analog input
// pins are a separate set.

// ATMEL ATTINY85
//
//                    +-\/-+
// (ADC0/reset) PB5  1|    |8  VCC
//      (ADC3)  PB3  2|    |7  PB2 (ADC1/SCK)
//      (ADC2)  PB4  3|    |6  PB1 (DO/ MISO / OC1A)
//              GND  4|    |5  PB0 (DI/ MOSI / ^OC1A)
//                  +----+
//
// these arrays map port names (e.g. port B) to the
// appropriate addresses for various functions (e.g. reading
// and writing)
const uint16_t PROGMEM port_to_mode_PGM[] = {
	NOT_A_PORT,
	NOT_A_PORT,
	(uint16_t) &DDRB,
};

const uint16_t PROGMEM port_to_output_PGM[] = {
	NOT_A_PORT,
	NOT_A_PORT,
	(uint16_t) &PORTB,
};

const uint16_t PROGMEM port_to_input_PGM[] = {
	NOT_A_PORT,
	NOT_A_PORT,
	(uint16_t) &PINB,
};

const uint8_t PROGMEM digital_pin_to_port_PGM[] = {
  0, /* 0 - x */
  PB, /* 1 - reset */
  PB, /* 2 */
  PB,
  0, /* 4 - VCC */
  PB, /* 5 */
  PB,
  PB,
  0, /* VCC */
};

const uint8_t PROGMEM digital_pin_to_bit_mask_PGM[] = {
  _BV(0), /* 0, x */
  _BV(5), /* 1, reset */
  _BV(3), /* 2 */
  _BV(4),
  _BV(0), /* 4 GND */
  _BV(0), /* 5 */
  _BV(1), /* 6 */
  _BV(2), /* 7 */
  _BV(0), /* 8 VCC  */
};

const uint8_t PROGMEM digital_pin_to_timer_PGM[] = {
  NOT_ON_TIMER, /* 0 */
  NOT_ON_TIMER,
  NOT_ON_TIMER,  
  TIMER1B,      
  NOT_ON_TIMER,
  TIMER0A,
  TIMER0B,
  NOT_ON_TIMER,
  NOT_ON_TIMER, 
};

#endif

// These serial port names are intended to allow libraries and architecture-neutral
// sketches to automatically default to the correct port name for a particular type
// of use.  For example, a GPS module would normally connect to SERIAL_PORT_HARDWARE_OPEN,
// the first hardware serial port whose RX/TX pins are not dedicated to another use.
//
// SERIAL_PORT_MONITOR        Port which normally prints to the Arduino Serial Monitor
//
// SERIAL_PORT_USBVIRTUAL     Port which is USB virtual serial
//
// SERIAL_PORT_LINUXBRIDGE    Port which connects to a Linux system via Bridge library
//
// SERIAL_PORT_HARDWARE       Hardware serial port, physical RX & TX pins.
//
// SERIAL_PORT_HARDWARE_OPEN  Hardware serial ports which are open for use.  Their RX & TX
//                            pins are NOT connected to anything by default.
#define SERIAL_PORT_MONITOR   None
#define SERIAL_PORT_HARDWARE  None

#endif
