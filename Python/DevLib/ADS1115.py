#!/usr/bin/env python
# -*- coding: utf-8 -*-
# This driver reads the ADS1115 16-bit Sigma-Delta ADC with internal programmable gain amplifier.
#
#
# Sources:
# Datasheet: http://www.ti.com/lit/ds/symlink/ads1115.pdf
# Adafruit:  https://www.adafruit.com/product/1085
#            https://github.com/adafruit/Adafruit_Python_ADS1x15/blob/master/Adafruit_ADS1x15/ADS1x15.py
#
# The ads1115 (and ads111x family, and ads101x family) is a 16-bit precision ADC, with a maximum sample
# rate of 860 samples per second, and VDD in the range of 2 - 5.5 V.
# Conversions can be in single-shot or continuous-conversion mode.
# Inputs are either 4 single ended, or two differential signals.
#
# The ADS1115 has an internal voltage reference. No external reference is needed.
# Although the programmable gain amplifier has settings larger than Vdd, the analog inputs
# shoud never go above Vdd, the supply voltage, which has a maximum of 5.5V (absolute max is 7V)
# The analog inputs should also never go below GND.
#
# The Conversion Register is 16-bits at address 0x00
#
# The Control Register is 16bits and is at Address 0x01
#
# Input Multiplexer:
# Control Register bits 14:12
# 000 : AINP = AIN0 and AINN = AIN1 (default)
# 001 : AINP = AIN0 and AINN = AIN3
# 010 : AINP = AIN1 and AINN = AIN3
# 011 : AINP = AIN2 and AINN = AIN3
# 100 : AINP = AIN0 and AINN = GND
# 101 : AINP = AIN1 and AINN = GND
# 110 : AINP = AIN2 and AINN = GND
# 111 : AINP = AIN3 and AINN = GND
#
# Gain settings: FSR = Full Scale Reading.
# Control Register bits: 11:9
# 000 : FSR = ±6.144 V
# 001 : FSR = ±4.096 V
# 010 : FSR = ±2.048 V (default)
# 011 : FSR = ±1.024 V
# 100 : FSR = ±0.512 V
# 101 : FSR = ±0.256 V
# 110 : FSR = ±0.256 V
# 111 : FSR = ±0.256 V
#
# Data Conversion Rate for continuous operation.
# Control Register bit 8 = 0, continuous conversion mode, =1: single shot mode.
# Control Register bits: 7:5
# 000 : 8 SPS
# 001 : 16 SPS
# 010 : 32 SPS
# 011 : 64 SPS
# 100 : 128 SPS (default)
# 101 : 250 SPS
# 110 : 475 SPS
# 111 : 860 SPS
#
# There is a low-theshold and high-theshold register at address 0x02 and 0x03
#
# Note about I2C:
# Althought there is an smbus.read_word_data() which reads 2 bytes, and a corresponding
# smbus.write_word_data(), these function appear to read/write the bytes in the wrong order.
#
# TODO:
#   * Improve the decoding/encoding of the control register by using a bit structure.
#   * Further reduce the number of reads of the control register.
#
import time
import smbus
import ctypes

class ADS1115(object):
    """ADS1115 16-bit ADC
    Parameters: bus (default=1), addr (default = 0x48)"""

    # Maping of gain values to config register values.
    ADS1115_CONFIG_FULLSCALE = {
        6.144:   0b000<<9,
        4.096:   0b001<<9,
        2.048:   0b010<<9,
        1.024:   0b011<<9,
        0.512:   0b100<<9,
        0.256 :  0b101<<9
    }
    ADS1115_CONFIG_FULLSCALE_REV = {v: k for k, v in ADS1115_CONFIG_FULLSCALE.items()}
    # Mapping of data/sample rate to config register values for ADS1015 (faster).
    # Mapping of data/sample rate to config register values for ADS1115 (slower).
    ADS1115_CONFIG_DATARATE = {
        8:    0b000<<5,
        16:   0b001<<5,
        32:   0b010<<5,
        64:   0b011<<5,
        128:  0b100<<5,
        250:  0b101<<5,
        475:  0b110<<5,
        860:  0b111<<5
    }
    ADS1115_CONFIG_DATARATE_REV = {v: k for k, v in ADS1115_CONFIG_DATARATE.items()}

    def __init__(self, bus=1, address=0x48):
        try:
            self._bus = smbus.SMBus(bus)
        except IOError:
            print("Error opening SMBus {}. Please make sure the Raspberry Pi is setup to read this bus.".format(bus))
            return(None)

        self._address=address            # Set by the hardware = 0b1101000
        self._buf=[]
        self._conversion_mode = self.read_mode()      # The conversion mode. Stored for convenience
        self._data_rate = self.read_rate()            # The conversion rate. Stored for convenience
        self._FSR = self.read_fullscale()             # The full scale. Stored for convenience.
        self._input,self._differential = self.read_input() # Input channel and differentual mode ,,

    def _read_adc(self):
        """ Read and return the conversion register."""
        val=self._bus.read_i2c_block_data(self._address,0x00,2) # Read 2 bytes from i2c
        res = (val[0]<<8) + val[1]
        if val[0] & 0x80:     # The ADC returns a signed, ones complement, number.
            res -= 0xFFFF -1  # This is the equivalent of fixing up the ones complement.

        return(res)

    def _read_control(self):
        """ Read and return the control register."""
        val=self._bus.read_i2c_block_data(self._address,0x01,2) # Read 2 bytes from i2c
        res = (val[0]<<8) + val[1]
        return(res)

    def _set_control(self,control):
        """ Set the control register on the chip.

        Parameters:
        ------------
        control: int (16-bits)
            The 16 bits to set the control register to.
        """
        val = [((control>>8) & 0xFF),(control & 0xFF)]
        self._bus.write_i2c_block_data(self._address,0x01,val)

    def _set_control_bits(self,bit_value,bit_mask):
        """ Set specific bits in the control register. The mask, is a set of 1 Bits
        that are to be manipulated, and the bit_value is the new value.
        Example: Set bits 11:9 to "101": _set_control_bits(0b101<<9,0b111<<9)

        Parameters:
        -----------
        bit_value: int (16-bits)
                Value the bits are to be set to.
        bit_mask:
                Mask of the bits to be set.
        """
        control = self._read_control()
        control &= ( bit_mask ^ 0xFFFF )  # Invert the bit_mask, then and to control, clearing bits.
        control |= bit_value              # Set the appropriate bits.
        self._set_control(control)        # Write back to register.

    def set_mode(self,mode=1):
        """Set the read mode for the conversions.

        Parameters:
        -----------
         mode: int
            Set the conversion mode: 1 use single-shot mode, 0 use continuous mode.
        """
        assert mode==0 or mode==1
        self._conversion_mode = mode
        self._set_control_bits(mode<<8,0b01<<8)

    def read_mode(self,control=None):
        """Read and return the conversion mode from the control register.
        Mode = 0 (False) is continuous mode.
        Mode = 1 (True)  is single shot mode."""
        if control is None:
            control = self._read_control()
        return( (control& (0b01<<8))>0 )

    def get_mode(self):
        """Return the stored conversion mode. """
        return(self._conversion_mode)

    def set_rate(self,data_rate):
        """Set the reading rate for continuous conversion mode.
        Does not change the mode unless data_rate =0, which sets mode to 1 (single conversion)

        Parameters:
        -----------
        data_rate: int
            Set the data rate for continuous mode. Must be one of
            0, 8,16,32,64,128,250,475,860, with 0 forcing mode=1
        """
        if data_rate == 0:
            self.set_read_mode(1)
            return
        else:
            if not data_rate in self.ADS1115_CONFIG_DATARATE:
                raise ValueError("The data rate must be 0 or one from the list {}".format(self.ADS1115_CONFIG_DATARATE))
        self._data_rate = data_rate
        rate_bits = self.ADS1115_CONFIG_DATARATE[data_rate]
        self._set_control_bits(rate_bits,0b111<<5)

    def read_rate(self,control=None):
        """Read and return the data rate from the control register."""
        if control is None:
            control = self._read_control()
        rate_bits =  control & 0b111 << 5
        self._data_rate = self.ADS1115_CONFIG_DATARATE_REV[rate_bits]
        return(self._data_rate)

    def get_rate(self):
        """Return the stored data rate."""
        return(self._data_rate)

    def set_input(self,channel,differential=0):
        """Select which of the 4 inputs to read.
        If differential = 1, then the difference is read according to the table:
        channel = 0  =>  AIN0 - AIN1
        channel = 1  =>  AIN0 - AIN3
        channel = 2  =>  AIN1 - AIN3
        channel = 3  =>  AIN2 - AIN3

        Parameters:
        -----------
        channel: int
            Channel to read, must be 0,1,2,or 3
        differential: Boolean
            Whether to read differential (1 or True) or absolute (0 or False).
        """
        assert 0<= channel < 4
        self._input = channel
        self._differential = differential
        if not differential:
            channel += 0b100
        self._set_control_bits(channel<<12,0b111<<12)

    def read_input(self,control=None):
        """Read and return the current input selection.
        Returns: (channel,differential)
        """
        if control is None:
            control = self._read_control()
        mux = (control & (0b111<<12))>>12
        self._input =mux&0b011
        self._differential = not ((mux&0b100)>>2)
        return (self._input,self._differential)

    def get_input(self):
        """Return the stored input channel and differential setting."""
        return (self._input,self._differential)

    def set_fullscale(self,full_scale):
        """Select the full scale (FSR) for the programmable gain amplifier.

        Parameters:
        -----------
        full_scale: float
            Value for the full scale (maximum) of the ADC. This must be one of:
            0.256,0.512,1.024,2.048,4.096,6.144 (units are volts).
            Note that you cannot input more than Vdd on an input irrespective of the
            full_scale setting.
        """
        if not full_scale in self.ADS1115_CONFIG_FULLSCALE:
            raise ValueError("full_scale must be one of {}".format(self.ADS1115_CONFIG_FULLSCALE))

        self._FSR = full_scale
        pga = self.ADS1115_CONFIG_FULLSCALE[full_scale]
        self._set_control_bits(pga,0b111<<9)

    def read_fullscale(self,control=None):
        """Read the full scale setting from the control register."""
        if control is None:
            control = self._read_control()
        pga = control & (0b111<<9)
        self._FSR =self.ADS1115_CONFIG_FULLSCALE_REV[pga]
        return(self._FSR)

    def get_fullscale(self):
        """Return the stored fullscale setting"""
        return(self._FSR)

    def read_adc(self,input=None):
        """Read the ADC for given input, without changing other settings in the control register.
        If input=None, read the current input.
        Returns the raw ADC value as a 16-bit integer.
        If conversion mode is 1 (single shot) then trigger a conversion, and wait for it
        to complete, then return the conversion value.
        If conversion mode is 0 (continuous) then read the adc directly, returning the
        last read value."""

        if input is not None and input != self.get_input()[0]:
            self.set_input(input)

        if self._conversion_mode == 1:   # Single shot mode.
            # We need to write a 1 to bit 15 of the control register.
            # to start the conversion.
            control = self._read_control()
            control |= 0b01<<15         # Set Bit 15, going out of low power mode.
            self._set_control(control)  # Start conversion.
            time.sleep(1/self._data_rate + 0.0001)
            conv_done = False
            while not conv_done:
                control = self._read_control()
                conv_done = ((control & 0x8000)>0)   # Check bit 15
            adc_raw = self._read_adc()
            return(adc_raw)
        else:
            return(self._read_adc())

    def read_volts(self,input=None):
        """Read the ADC for given input and convert the number to volts according to the
        setting of the full scale. """

        return( self.get_fullscale()*self.read_adc(input)/0x7FFF )

    def __str__(self):
        """Return a string with a description of the current status. """
        out = "ADS115: full scale = {:6.5f}  data rate = {:3d}  input = {:1d}".format(self.get_fullscale(),self.get_rate(),self.get_input()[0])
        out +="diff={:1d} value = 0x{:04x} volts={:7.6f}".format(self.get_input()[1],self.read_adc(),self.read_volts())
        return(out)

    @property
    def adc(self):
        """ADC value for current input as integer"""
        return( self.read_adc() )

    @property
    def volts(self):
        """ADC value for current input converted to volts."""
        return( self.read_volts() )

    @property
    def accuracy(self):
        """The fractional voltage of the least significant bit. """
        return(self.get_fullscale()/float(0x7FFF))

    @property
    def input(self):
        """The current input channel """
        return(self._input)

    @input.setter
    def input(self, inp):
        """Set the input channel """
        self.set_input(inp)

    @property
    def rate(self):
        """The data conversion rate in samples per seconds. See set_rate()."""
        return(self._data_rate)

    @rate.setter
    def rate(self,rate):
        """Set the data conversion rate in sample per seconds.See set_rate()."""
        self.set_rate(rate)

    @property
    def fullscale(self):
        """The fullscale of the data conversion. See set_fullscale()."""
        return(self._FSR)

    @fullscale.setter
    def fullscale(self,fsr):
        """Set the fillscale of the data conversion, see set_fullscale()."""
        self.set_fullscale(fsr)
