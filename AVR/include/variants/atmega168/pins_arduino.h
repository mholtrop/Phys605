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

#define NUM_DIGITAL_PINS            20
#define NUM_ANALOG_INPUTS           6
#define analogInputToDigitalPin(p)  ((p < 6) ? (p) + 23 : -1)

#define digitalPinHasPWM(p)         ((p) == 5 || (p) == 11 || (p) == 12 || (p) == 15 || (p) == 16 || (p) == 17)

static const uint8_t SS   = 16;
static const uint8_t MOSI = 17;
static const uint8_t MISO = 18;
static const uint8_t SCK  = 19;

static const uint8_t SDA = 27;
static const uint8_t SCL = 28;
#define LED_BUILTIN -1

static const uint8_t A0 = 23;
static const uint8_t A1 = 24;
static const uint8_t A2 = 25;
static const uint8_t A3 = 26;
static const uint8_t A4 = 27;
static const uint8_t A5 = 28;
static const uint8_t A6 = -1;
static const uint8_t A7 = -1;

#define digitalPinToPCICR(p)    ( (((p) >= 2  ) && ((p) <= 6 )) || \
                                  (((p) >= 11 ) && ((p) <= 19)) || \
                                  (((p) >= 23 ) && ((p) <= 28)) ?  (&PCICR) : ((uint8_t *)0))
                                                                 
#define digitalPinToPCICRbit(p) (( ((p)>=2   && (p) <= 6) || ((p)>=11 && (p)<= 13 ) ) ? 2 : (( (p)>=14 && (p) <= 19 ) ? 0 : ( ( (p)<=28)?1:0)))
#define digitalPinToPCMSK(p)    \
  (( ((p)>=2   && (p) <= 6) || ((p)>=11 && (p)<= 13 ) ) ? (&PCMSK2) :	\
  (( ((p)>= 14 && (p) <= 19) || (p) == 9 || (p) == 10) ? (&PCMSK0) :	\
   ( ((p)>= 23 && (p) <= 28) || (p) == 1) ? (&PCMSK1) : ((uint8_t *)0)))
/* NOTE: Not assigining pin 1 = reset, but could be set to PC6 */
#define digitalPinToPCMSKbit(p)    (( (p) >=2  && (p) <= 6 )  ? ((p)-2)    : \
                                   (( (p) >= 9 && (p) <= 10)  ? ((p)-3)    : \
				   (( (p) >=11 && (p) <=13 )  ? ((p)-6)    : \
				   (( (p) <= 19 )             ? ((p) - 14) : \
				    ( (p) - 23  )   ))))

#define digitalPinToInterrupt(p)  ((p) == 4 ? 0 : ((p) == 5 ? 1 : NOT_AN_INTERRUPT))

#ifdef ARDUINO_MAIN

// On the Arduino board, digital pins are also used
// for the analog output (software PWM).  Analog input
// pins are a separate set.

// ATMEL ATMEGA8 & 168 / ARDUINO
//
//                  +-\/-+
//            PC6  1|    |28  PC5 (AI 5)
//      (D 0) PD0  2|    |27  PC4 (AI 4)
//      (D 1) PD1  3|    |26  PC3 (AI 3)
//      (D 2) PD2  4|    |25  PC2 (AI 2)
// PWM+ (D 3) PD3  5|    |24  PC1 (AI 1)
//      (D 4) PD4  6|    |23  PC0 (AI 0)
//            VCC  7|    |22  GND
//            GND  8|    |21  AREF
//            PB6  9|    |20  AVCC
//            PB7 10|    |19  PB5 (D 13)
// PWM+ (D 5) PD5 11|    |18  PB4 (D 12)
// PWM+ (D 6) PD6 12|    |17  PB3 (D 11) PWM
//      (D 7) PD7 13|    |16  PB2 (D 10) PWM
//      (D 8) PB0 14|    |15  PB1 (D 9) PWM
//                  +----+
//
// (PWM+ indicates the additional PWM pins on the ATmega168.)

// ATMEL ATMEGA1280 / ARDUINO
//
// 0-7 PE0-PE7   works
// 8-13 PB0-PB5  works
// 14-21 PA0-PA7 works 
// 22-29 PH0-PH7 works
// 30-35 PG5-PG0 works
// 36-43 PC7-PC0 works
// 44-51 PJ7-PJ0 works
// 52-59 PL7-PL0 works
// 60-67 PD7-PD0 works
// A0-A7 PF0-PF7
// A8-A15 PK0-PK7


// these arrays map port names (e.g. port B) to the
// appropriate addresses for various functions (e.g. reading
// and writing)
const uint16_t PROGMEM port_to_mode_PGM[] = {
	NOT_A_PORT,
	NOT_A_PORT,
	(uint16_t) &DDRB,
	(uint16_t) &DDRC,
	(uint16_t) &DDRD,
};

const uint16_t PROGMEM port_to_output_PGM[] = {
	NOT_A_PORT,
	NOT_A_PORT,
	(uint16_t) &PORTB,
	(uint16_t) &PORTC,
	(uint16_t) &PORTD,
};

const uint16_t PROGMEM port_to_input_PGM[] = {
	NOT_A_PORT,
	NOT_A_PORT,
	(uint16_t) &PINB,
	(uint16_t) &PINC,
	(uint16_t) &PIND,
};

const uint8_t PROGMEM digital_pin_to_port_PGM[] = {
  0,  /* 0 - x */
  PC, /* 1 - reset */
  PD, /* 2 */
  PD,
  PD,
  PD,
  PD,
  0, /* 7 - VCC */
  0, /* 8 - GND */
  0, /* 9 - XTAL */
  0, /* 10 - XTAL */
  PD,/* 11 */
  PD,/* 12 */
  PD,/* 13 */
  PB,/* 14 */
  PB,
  PB,
  PB,
  PB,
  PB,
  0 ,/* 20 - AVCC */
  0 ,/* 21 - AREF */
  0 ,/* 22 - GND  */
  PC,/* 23 */
  PC,
  PC,
  PC,
  PC,
  PC,/* 28 */
};

const uint8_t PROGMEM digital_pin_to_bit_mask_PGM[] = {
	_BV(0), /* 0, x */
	_BV(0), /* 1, reset */
	_BV(0), /* 2 */
	_BV(1),
	_BV(2),
	_BV(3),
	_BV(4), /* 6 */
	_BV(0), /* 7, VCC  */
	_BV(0), /* 8, GND  */
	_BV(0), /* 9, XTAL  */
	_BV(0), /*10, XTAL  */
	_BV(5), /* 11 */
	_BV(6), /* 12 */
	_BV(7), /* 13 */
	_BV(0), /* 14, port B */
	_BV(1),
	_BV(2),
	_BV(3),
	_BV(4),
	_BV(5), /* 19 */
	_BV(0), /* 20, AVCC */
	_BV(0), /* 21, AREF */
	_BV(0), /* 22, GND  */
	_BV(0), /* 23, port C */
	_BV(1),
	_BV(2),
	_BV(3),
	_BV(4),
	_BV(5), /* 28 */
};

const uint8_t PROGMEM digital_pin_to_timer_PGM[] = {
	NOT_ON_TIMER, /* 0 - port D */
	NOT_ON_TIMER,
	NOT_ON_TIMER,
	NOT_ON_TIMER,
	NOT_ON_TIMER,
	TIMER2B, 	// on the ATmega168, digital pin 5 has hardware pwm
	NOT_ON_TIMER,
	NOT_ON_TIMER,
	NOT_ON_TIMER,
	NOT_ON_TIMER,
	NOT_ON_TIMER,
	TIMER0B,      /* 11 PCINT21/OC0B/T1/  PD5 */
	TIMER0A,      /* 12 PCINT22/OC0A/AIN0 PD6 */
	NOT_ON_TIMER, /* 13 */
	NOT_ON_TIMER, /* 14 */
	TIMER1A,      /* 15 */
	TIMER1B,      /* 16 */
	TIMER2A,      /* 17 */
	NOT_ON_TIMER, /* 18 */
	NOT_ON_TIMER, /* 19 */
	NOT_ON_TIMER, /* 20 AVCC */
	NOT_ON_TIMER, /* 21 AREF */
	NOT_ON_TIMER, /* 22 GND */
	NOT_ON_TIMER, /* 23 */
	NOT_ON_TIMER, /* 24 */
	NOT_ON_TIMER, /* 25 */
	NOT_ON_TIMER, /* 26 */
	NOT_ON_TIMER, /* 27 */
	NOT_ON_TIMER, /* 28 */
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
#define SERIAL_PORT_MONITOR   Serial
#define SERIAL_PORT_HARDWARE  Serial

#endif
