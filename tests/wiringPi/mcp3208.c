#include <stdio.h>
#include <stdint.h>

#include <wiringPi.h>
#include <wiringPiSPI.h>

#define ADC_SPI_CHANNEL 1
#define ADC_SPI_SPEED 500000
#define ADC_NUM_CHANNELS 8


uint16_t readADC(_channel){
	uint8_t spi_data[3];
	uint8_t input_mode = 1; // single ended = 1, differential = 0
	uint16_t result;

	if(_channel > 7 | _channel < 0){
		return -1;
	}


	spi_data[0] = 0x04; // start flag
	spi_data[0] |= (input_mode<<1); // shift input_mode
	spi_data[0] |= (_channel>>2) & 0x01; // add msb of channel in our first command byte

	spi_data[1] = _channel<<6;
	spi_data[2] = 0x00;

	wiringPiSPIDataRW(ADC_SPI_CHANNEL, spi_data, 3);

	result = (spi_data[1] & 0x0f)<<8 | spi_data[2];
	return result;
}

int main(){
	
	wiringPiSetupSys();
	wiringPiSPISetup(ADC_SPI_CHANNEL, ADC_SPI_SPEED);

	for(;;){
		int i;
		for(i = 0; i < ADC_NUM_CHANNELS; i++){
			int val;
			val = readADC(i);
			// printf("chan%d %d ", i, val);
		}
		// printf("\n");
		delay(1);
	}
}