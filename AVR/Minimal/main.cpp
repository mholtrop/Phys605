/*
 *  Minimal.cpp
 *
 *  Minimal program for directly talking to an Atmega328p
 *
 *  This code shows the "advanced" way of programming an AVR microprocessor.
 *  We use the information from the datasheet and from the AVR Software Developement Kit (SDK)
 *
 *  To keep the ease of some function from the Arduino world, such as the Serial class, we import
 *  the Arduino header and link against the Arduino libraries.
 *
 *  Created on: April 2, 2015, updated April 17, 2019
 *      Author: Maurik
 */

#include <avr/io.h>
#include "Arduino.h"
#include "HardwareSerial.h"
#include "Sensirion.h"

int
main (void) {

  init(); // The Arduino init() function is needed for timer and delay(ms) to function properly.

  Serial.begin(115200);
  Serial.print("Hello this is the atmega328 starting up. V-0.0.2\n\r");

  // Set interrupts enabled.
  DDRB = 0x02;    // Pin PB1 = chip pin 15 is output. Put Scope here.
  PORTB = 0x02;   // ON
  PORTB = 0x00;   // OFF
  DDRD = 0x80;    // Pin PD7 = chip pin 13 is output. Put LED (w. resistor!) here.
  PORTD = 0x00;   // OFF

  Serial.print("Loop top..\n");

  int loopcount=0;
  while (1) {
      if( (loopcount++)%100 == 0){
        Serial.print("L=");
        Serial.println(loopcount);
      }
      Serial.print(".");
      for (unsigned char i = 0; i < 255; i++) {
        for (unsigned char i = 0; i < 255; i++) {  // Turn on and off PB1 port quickly 8 times for every change on PD7
	  PORTB &= 0xFD; // PB1 OFF
	  PORTB |= 0x02; // PB1 ON
	  PORTB &= 0xFD; // PB1 OFF
	  PORTB |= 0x02; // PB1 ON
	  PORTB &= 0xFD; // PB1 OFF
	  PORTB |= 0x02; // PB1 ON
	  PORTB &= 0xFD; // PB1 OFF
	  PORTB |= 0x02; // PB1 ON
	  PORTB &= 0xFD; // PB1 OFF
	  PORTB |= 0x02; // PB1 ON
	  PORTB &= 0xFD; // PB1 OFF
	  PORTB |= 0x02; // PB1 ON
	  PORTB &= 0xFD; // PB1 OFF
	  PORTB |= 0x02; // PB1 ON
	  PORTB &= 0xFD; // PB1 OFF
	  PORTB |= 0x02; // PB1 ON
	  PORTB &= 0xFD; // PB1 OFF

	  // Here is an even more advaced method of changing the output pins. 
	  // If you want absolete perfect control of the chip at maximum speed, you
	  // need to use Assembly language.
	  // Typically, we avoid doing this, and have the C compiler do the work.
	  //
	  //
        // Set bit 1 on PORTB 0x05 The _SFR_IO_ADDR subtracts 0x20 for port address
        // asm volatile(
        //     "sbi %0, %1 " "\n\t"
        //     "cbi %0, %1 " "\n\t"
        //     "sbi %0, %1 " "\n\t"
        //     "cbi %0, %1 " "\n\t"
        //     "sbi %0, %1 " "\n\t"
        //     "cbi %0, %1 " "\n\t"
        //     "nop " "\n\t"
        //     "nop " "\n\t"
        //     "nop " "\n\t"
        //     "nop " "\n\t"
        //     "nop " "\n\t"
        //     "nop " "\n\t"
        //     "nop " "\n\t"
        //     "nop " "\n\t"
        //     "sbi %2, %1 " "\n\t"  // Toggle the pin on port.
        //     "sbi %2, %1 " "\n\t"
        //     "sbi %2, %1 " "\n\t"
        //     "sbi %2, %1 " "\n\t"
        //     "sbi %2, %1 " "\n\t"
        //     "sbi %2, %1 " "\n\t"
        //     "sbi %2, %1 " "\n\t"
        //     "sbi %2, %1 " "\n\t"
        //     ::"I" (_SFR_IO_ADDR(PORTB)),"I" (PB1),"I" (_SFR_IO_ADDR(PINB))
        // );
      }
    PORTD ^= 0x80;  // XOR = toggle bit 7.
    }

  }
}

