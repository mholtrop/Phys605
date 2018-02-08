# Distributed with a free-will license.
# Use it any way you want, profit or free, provided it fits in the licenses of its associated works.
# BMP280
# This code is designed to work with the BMP280_I2CS I2C Mini Module available from ControlEverything.com.
# https://www.controleverything.com/content/Barometer?sku=BMP280_I2CSs#tabs-0-product_tabset-2


import smbus
import time

# Get I2C bus
bus = smbus.SMBus(1)


# I2C address of the device
BMP280_DEFAULT_ADDRESS				= 0x76

# BMP280 Register Map
BMP280_DIG_T1_LSB_REG				= 0x88 # Calibration Data
BMP280_DIG_T1_MSB_REG				= 0x89 # Calibration Data
BMP280_DIG_T2_LSB_REG				= 0x8A # Calibration Data
BMP280_DIG_T2_MSB_REG				= 0x8B # Calibration Data
BMP280_DIG_T3_LSB_REG				= 0x8C # Calibration Data
BMP280_DIG_T3_MSB_REG				= 0x8D # Calibration Data
BMP280_DIG_P1_LSB_REG				= 0x8E # Calibration Data
BMP280_DIG_P1_MSB_REG				= 0x8F # Calibration Data
BMP280_DIG_P2_LSB_REG				= 0x90 # Calibration Data
BMP280_DIG_P2_MSB_REG				= 0x91 # Calibration Data
BMP280_DIG_P3_LSB_REG				= 0x92 # Calibration Data
BMP280_DIG_P3_MSB_REG				= 0x93 # Calibration Data
BMP280_DIG_P4_LSB_REG				= 0x94 # Calibration Data
BMP280_DIG_P4_MSB_REG				= 0x95 # Calibration Data
BMP280_DIG_P5_LSB_REG				= 0x96 # Calibration Data
BMP280_DIG_P5_MSB_REG				= 0x97 # Calibration Data
BMP280_DIG_P6_LSB_REG				= 0x98 # Calibration Data
BMP280_DIG_P6_MSB_REG				= 0x99 # Calibration Data
BMP280_DIG_P7_LSB_REG				= 0x9A # Calibration Data
BMP280_DIG_P7_MSB_REG				= 0x9B # Calibration Data
BMP280_DIG_P8_LSB_REG				= 0x9C # Calibration Data
BMP280_DIG_P8_MSB_REG				= 0x9D # Calibration Data
BMP280_DIG_P9_LSB_REG				= 0x9E # Calibration Data
BMP280_DIG_P9_MSB_REG				= 0x9F # Calibration Data
BMP280_DIG_H1_REG					= 0xA1 # Calibration Data
BMP280_CHIP_ID_REG					= 0xD0 # Chip ID
BMP280_RST_REG						= 0xE0 # Softreset Register
BMP280_STAT_REG						= 0xF3 # Status Register
BMP280_CTRL_MEAS_REG				= 0xF4 # Control Measure Register
BMP280_CONFIG_REG					= 0xF5 # Configuration Register
BMP280_PRESSURE_MSB_REG				= 0xF7 # Pressure MSB
BMP280_PRESSURE_LSB_REG				= 0xF8 # Pressure LSB
BMP280_PRESSURE_XLSB_REG			= 0xF9 # Pressure XLSB
BMP280_TEMPERATURE_MSB_REG			= 0xFA # Temperature MSB
BMP280_TEMPERATURE_LSB_REG			= 0xFB # Temperature LSB
BMP280_TEMPERATURE_XLSB_REG			= 0xFC # Temperature XLSB

# BMP280 Control Measure Register Configuration
BMP280_P_OVERSAMPLE_NONE			= 0x00 # Skipped
BMP280_P_OVERSAMPLE_1				= 0x20 # Oversampling x 1
BMP280_P_OVERSAMPLE_2				= 0x40 # Oversampling x 2
BMP280_P_OVERSAMPLE_4				= 0x60 # Oversampling x 4
BMP280_P_OVERSAMPLE_8				= 0x80 # Oversampling x 8
BMP280_P_OVERSAMPLE_16				= 0xA0 # Oversampling x 16
BMP280_T_OVERSAMPLE_NONE			= 0x00 # Skipped
BMP280_T_OVERSAMPLE_1				= 0x04 # Oversampling x 1
BMP280_T_OVERSAMPLE_2				= 0x08 # Oversampling x 2
BMP280_T_OVERSAMPLE_4				= 0x0C # Oversampling x 4
BMP280_T_OVERSAMPLE_8				= 0x10 # Oversampling x 8
BMP280_T_OVERSAMPLE_16				= 0x14 # Oversampling x 16
BMP280_MODE_SLEEP					= 0x00 # Sleep Mode
BMP280_MODE_FORCED					= 0x01 # Forced Mode
BMP280_MODE_NORMAL					= 0x03 # Normal Mode

# BMP280 Configuration Register
BMP280_STANDBY_MS_0_5				= 0x00 # Standby Time = 0.5ms
BMP280_STANDBY_MS_10				= 0xC0 # Standby Time = 10ms
BMP280_STANDBY_MS_20				= 0xD0 # Standby Time = 20ms
BMP280_STANDBY_MS_62_5				= 0x20 # Standby Time = 62.5ms
BMP280_STANDBY_MS_125				= 0x40 # Standby Time = 125ms
BMP280_STANDBY_MS_250				= 0x60 # Standby Time = 250ms
BMP280_STANDBY_MS_500				= 0x80 # Standby Time = 500ms
BMP280_STANDBY_MS_1000				= 0xA0 # Standby Time = 1000ms
BMP280_FILTER_OFF					= 0x00 # Filter Off
BMP280_FILTER_X2					= 0x04 # Filter Coefficient = 2
BMP280_FILTER_X4					= 0x08 # Filter Coefficient = 4
BMP280_FILTER_X8					= 0x0C # Filter Coefficient = 8
BMP280_FILTER_X16					= 0x10 # Filter Coefficient = 16
BMP280_SPI3_EN						= 0x01 # Enables 3-wire SPI interface

class BMP280:
	def read_pres_temp_coeff(self):
		"""Read data back from BMP280_DIG_T1_LSB_REG(0x88), 24 bytes"""
		b1 = bus.read_i2c_block_data(BMP280_DEFAULT_ADDRESS, BMP280_DIG_T1_LSB_REG, 24)

		# Temp coefficients
		self.dig_T1 = b1[1] * 256 + b1[0]

		self.dig_T2 = b1[3] * 256 + b1[2]
		if self.dig_T2 > 32767 :
			self.dig_T2 -= 65536

		self.dig_T3 = b1[5] * 256 + b1[4]
		if self.dig_T3 > 32767 :
			self.dig_T3 -= 65536

		# Pressure coefficients
		self.dig_P1 = b1[7] * 256 + b1[6]

		self.dig_P2 = b1[9] * 256 + b1[8]
		if self.dig_P2 > 32767 :
			self.dig_P2 -= 65536

		self.dig_P3 = b1[11] * 256 + b1[10]
		if self.dig_P3 > 32767 :
			self.dig_P3 -= 65536

		self.dig_P4 = b1[13] * 256 + b1[12]
		if self.dig_P4 > 32767 :
			self.dig_P4 -= 65536

		self.dig_P5 = b1[15] * 256 + b1[14]
		if self.dig_P5 > 32767 :
			self.dig_P5 -= 65536

		self.dig_P6 = b1[17] * 256 + b1[16]
		if self.dig_P6 > 32767 :
			self.dig_P6 -= 65536

		self.dig_P7 = b1[19] * 256 + b1[18]
		if self.dig_P7 > 32767 :
			self.dig_P7 -= 65536

		self.dig_P8 = b1[21] * 256 + b1[20]
		if self.dig_P8 > 32767 :
			self.dig_P8 -= 65536

		self.dig_P9 = b1[23] * 256 + b1[22]
		if self.dig_P9 > 32767 :
			self.dig_P9 -= 65536

	def write_configuration(self):
		"""Select the Control Measure Register Configuration from the given provided value"""
		PRES_TEMP_SAMPLE = (BMP280_P_OVERSAMPLE_1 | BMP280_T_OVERSAMPLE_1 | BMP280_MODE_NORMAL)
		bus.write_byte_data(BMP280_DEFAULT_ADDRESS, BMP280_CTRL_MEAS_REG, PRES_TEMP_SAMPLE)

		"""Select the Configuration Register data from the given provided value"""
		TIME_CONFIG = (BMP280_STANDBY_MS_1000 | BMP280_FILTER_OFF)
		bus.write_byte_data(BMP280_DEFAULT_ADDRESS, BMP280_CONFIG_REG, TIME_CONFIG)

	def read_data(self):
		"""Read data back from BMP280_PRESSURE_MSB_REG(0xF7), 6 bytes
		Pressure MSB, Pressure LSB, Pressure xLSB, Temperature MSB, Temperature LSB, Temperature xLSB"""
		data = bus.read_i2c_block_data(BMP280_DEFAULT_ADDRESS, BMP280_PRESSURE_MSB_REG, 6)

		# Convert pressure and temperature data to 19-bits
		self.adc_p = ((data[0] * 65536) + (data[1] * 256) + (data[2] & 0xF0)) / 16
		self.adc_t = ((data[3] * 65536) + (data[4] * 256) + (data[5] & 0xF0)) / 16

	def result_calculation(self):
		"""Offset calculations for the final pressure and temperature"""

		# Temperature offset calculations
		var1 = ((self.adc_t) / 16384.0 - (self.dig_T1) / 1024.0) * (self.dig_T2)
		var2 = (((self.adc_t) / 131072.0 - (self.dig_T1) / 8192.0) * ((self.adc_t)/131072.0 - (self.dig_T1)/8192.0)) * (self.dig_T3)
		t_fine = (var1 + var2)
		cTemp = (var1 + var2) / 5120.0
		fTemp = cTemp * 1.8 + 32

		# Pressure offset calculations
		var1 = (t_fine / 2.0) - 64000.0
		var2 = var1 * var1 * (self.dig_P6) / 32768.0
		var2 = var2 + var1 * (self.dig_P5) * 2.0
		var2 = (var2 / 4.0) + ((self.dig_P4) * 65536.0)
		var1 = ((self.dig_P3) * var1 * var1 / 524288.0 + (self.dig_P2) * var1) / 524288.0
		var1 = (1.0 + var1 / 32768.0) * (self.dig_P1)
		p = 1048576.0 - self.adc_p
		p = (p - (var2 / 4096.0)) * 6250.0 / var1
		var1 = (self.dig_P9) * p * p / 2147483648.0
		var2 = p * (self.dig_P8) / 32768.0
		pressure = (p + (var1 + var2 + (self.dig_P7)) / 16.0) / 100

		return {'p' : pressure, 'c' : cTemp, 'f' : fTemp}

from BMP280 import BMP280
bmp280 = BMP280()

while True :
	bmp280.read_pres_temp_coeff()
	bmp280.write_configuration()
	bmp280.read_data()
	data = bmp280.result_calculation()
	print "Pressure : %.2f hPa"%(data['p'])
	print "Temperature in Celsius : %.2f C"%(data['c'])
	print "Temperature in Fahrenheit : %.2f F"%(data['f'])
	print " ***************************************** "
	time.sleep(0.7)
