/** Simple I2C example to read the time from a DS3231 module
* Written by Derek Molloy for the book "Exploring Raspberry Pi" */

#include<stdio.h>
#include<fcntl.h>
#include<sys/ioctl.h>
#include<linux/i2c.h>
#include<linux/i2c-dev.h>
#define BUFFER_SIZE 19

// the time is in the registers in decimal form
int bcdToDec(char b) { return (b/16)*10 + (b%16); }

int main(){
   int file;
   int i;
   
   printf("Starting the DS3231 test application\n");
   if((file=open("/dev/i2c-1", O_RDWR)) < 0){
      perror("failed to open the bus\n");
      return 1;
   }
   if(ioctl(file, I2C_SLAVE, 0x68) < 0){
      perror("Failed to connect to the sensor\n");
      return 1;
   }
   char writeBuffer[1] = {0x00};
   if(write(file, writeBuffer, 1)!=1){
      perror("Failed to reset the read address\n");
      return 1;
   }
   char buf[BUFFER_SIZE];
   if(read(file, buf, BUFFER_SIZE)!=BUFFER_SIZE){
      perror("Failed to read in the buffer\n");
      return 1;
   }

   for(i=0;i<BUFFER_SIZE;++i){
     printf("A:0x%02X = 0x%02x (%3d) \n",i,buf[i],buf[i]);
   }
   printf("\n");

   printf("The RTC time is %02d:%02d:%02d (%1d) %4d-%02d-%02d\n", bcdToDec(buf[2]),
	  bcdToDec(buf[1]), bcdToDec(buf[0]),buf[3],(buf[5]&0x80==0x80?100:0)+1900+bcdToDec(buf[6]),
	  bcdToDec(buf[5]&0x1F),bcdToDec(buf[4]));
   printf("The AL1 time is %02d:%02d:%02d (%1d) \n", bcdToDec(buf[9]),
	  bcdToDec(buf[8]), bcdToDec(buf[7]),buf[10]);
   printf("The AL2 time is %02d:%02d:%02d (%1d) \n", bcdToDec(buf[12]),
	  bcdToDec(buf[11]), 0,buf[13]);
   float temperature = buf[0x11] + ((buf[0x12]>>6)*0.25);
   printf("The temperature is %.2f°C\n", temperature);
   close(file);
   return 0;
}
