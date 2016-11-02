/*
 *  Minimal.cpp
 *
 *  Minimal program for directly talking to an Atmega168
 *
 *  Created on: April 2, 2015
 *      Author: Maurik
 */

#include <avr/io.h>
#include "Arduino.h"
#include "HardwareSerial.h"

int
main (void) {

  sei();  // Enable interrupts:  __asm__ __volatile__ ("sei" ::: "memory");
  Serial.begin(115200);
  Serial.print("Hello this is the atmega168 starting up. V-0.0.2\n");

  // Set interrupts enabled.
  DDRB = 0x02;                   // Scope to PB1
  PORTB = 0x02;   // ON
  DDRD = 0x80; // 0b10000000; // PD7 is output.
  PORTD = 0x80; // ON

  Serial.print("Loop top..\n");
  int loopcount=0;
  while (1) {
      if( (loopcount++)%100 == 0){
        Serial.print("L=");
        Serial.println(loopcount);
      }
      Serial.print(".");
      for (unsigned char i = 0; i < 255; i++) {
        for (unsigned char i = 0; i < 255; i++) {
//        PORTB &= 0xFD; // PB1 OFF
//        PORTB |= 0x02; // PB1 ON
//        PORTB &= 0xFD; // PB1 OFF
//        PORTB |= 0x02; // PB1 ON
//        PORTB &= 0xFD; // PB1 OFF
//        PORTB |= 0x02; // PB1 ON


          // Set bit 1 on PORTB 0x05 The _SFR_IO_ADDR subtracts 0x20 for port address
        asm volatile(
            "sbi %0, %1 " "\n\t"
            "cbi %0, %1 " "\n\t"
            "sbi %0, %1 " "\n\t"
            "cbi %0, %1 " "\n\t"
            "sbi %0, %1 " "\n\t"
            "cbi %0, %1 " "\n\t"
            "nop " "\n\t"
            "nop " "\n\t"
            "nop " "\n\t"
            "nop " "\n\t"
            "nop " "\n\t"
            "nop " "\n\t"
            "nop " "\n\t"
            "nop " "\n\t"
            "sbi %2, %1 " "\n\t"  // Toggle the pin on port.
            "sbi %2, %1 " "\n\t"
            "sbi %2, %1 " "\n\t"
            "sbi %2, %1 " "\n\t"
            "sbi %2, %1 " "\n\t"
            "sbi %2, %1 " "\n\t"
            "sbi %2, %1 " "\n\t"
            "sbi %2, %1 " "\n\t"
            ::"I" (_SFR_IO_ADDR(PORTB)),"I" (PB1),"I" (_SFR_IO_ADDR(PINB))
        );
      }
    }
    PORTD ^= 0x80;  // XOR = toggle bit 7.
  }
}

