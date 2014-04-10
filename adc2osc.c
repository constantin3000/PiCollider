#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

// for void complain()
#include <stdarg.h>

#include <wiringPi.h>
#include <wiringPiSPI.h>

#include "osc/htmsocket.h"
#include "osc/OSC-client.h"

#define ADC_SPI_CHANNEL 1
#define ADC_SPI_SPEED 500000
#define ADC_NUM_CHANNELS 8

// OSC defines
#define SC_BUFFER_SIZE 32000
#define MAX_ARGS 64

typedef struct {
    enum {INT, FLOAT, STRING} type;
    union {
        int i;
        float f;
        char *s;
    } datum;
} typedArg;

int WriteMessage(OSCbuf *buf, char *messageName, int numArgs, typedArg *args);
void SendBuffer(void *htmsocket, OSCbuf *buf);
void SendData(void *htmsocket, int size, char *data);
void fatal_error(char *s);
void complain(char *s, ...);

static char bufferForOSCbuf[SC_BUFFER_SIZE];

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


int WriteMessage(OSCbuf *buf, char *messageName, int numArgs, typedArg *args) {
    int j, returnVal;

    returnVal = 0;

#ifdef DEBUG
    printf("WriteMessage: %s ", messageName);

     for (j = 0; j < numArgs; j++) {
        switch (args[j].type) {
            case INT:
	    printf("%d ", args[j].datum.i);
            break;

            case FLOAT:
	    printf("%f ", args[j].datum.f);
            break;

            case STRING:
	    printf("%s ", args[j].datum.s);
            break;

            default:
            fatal_error("Unrecognized arg type");
            exit(5);
        }
    }
    printf("\n");
#endif

	/* First figure out the type tags */
	char typeTags[MAX_ARGS+2];
	int i;

	typeTags[0] = ',';

	for (i = 0; i < numArgs; ++i) {
	    switch (args[i].type) {
		case INT:
		typeTags[i+1] = 'i';
		break;

		case FLOAT:
		typeTags[i+1] = 'f';
		break;

		case STRING:
		typeTags[i+1] = 's';
		break;

		default:
		fatal_error("Unrecognized arg type");
		exit(5);
	    }
	}
	typeTags[i+1] = '\0';
	    
	returnVal = OSC_writeAddressAndTypes(buf, messageName, typeTags);
	if (returnVal) {
	    complain("Problem writing address: %s\n", OSC_errorMessage);
	}
    

     for (j = 0; j < numArgs; j++) {
        switch (args[j].type) {
            case INT:
            if ((returnVal = OSC_writeIntArg(buf, args[j].datum.i)) != 0) {
		return returnVal;
	    }
            break;

            case FLOAT:
            if ((returnVal = OSC_writeFloatArg(buf, args[j].datum.f)) != 0) {
		return returnVal;
	    }
            break;

            case STRING:
            if ((returnVal = OSC_writeStringArg(buf, args[j].datum.s)) != 0) {
		return returnVal;
	    }
            break;

            default:
            fatal_error("Unrecognized arg type");
            exit(5);
        }
    }

    return returnVal;
}

void SendBuffer(void *htmsocket, OSCbuf *buf) {
#ifdef DEBUG
    printf("Sending buffer...\n");
#endif
    if (OSC_isBufferEmpty(buf)) return;
    if (!OSC_isBufferDone(buf)) {
	fatal_error("SendBuffer() called but buffer not ready!");
	exit(5);
    }
    SendData(htmsocket, OSC_packetSize(buf), OSC_getPacket(buf));
}

void SendData(void *htmsocket, int size, char *data) {
    if (!SendHTMSocket(htmsocket, size, data)) {
        perror("Couldn't send out socket: ");
        CloseHTMSocket(htmsocket);
        exit(3);
    }
}

void fatal_error(char *s) {
    fprintf(stderr, "%s\n", s);
    exit(4);
}

void complain(char *s, ...) {
    va_list ap;
    va_start(ap, s);
    vfprintf(stderr, s, ap);
    va_end(ap);
}

int main(){
	void *htmsocket;
    OSCbuf buf[1];
    typedArg args[ADC_NUM_CHANNELS];
    typedArg values[ADC_NUM_CHANNELS];


	int i;
    for(i = 0; i < ADC_NUM_CHANNELS; i++){
		values[i].type = INT;
	}

	htmsocket = OpenHTMSocket("192.168.1.35", 57120);
    if (!htmsocket) {
        perror("Couldn't open socket: ");
        exit(3);
    }

    OSC_initBuffer(buf, SC_BUFFER_SIZE, bufferForOSCbuf);


	wiringPiSetupSys();
	wiringPiSPISetup(ADC_SPI_CHANNEL, ADC_SPI_SPEED);

	for(;;){
		for(i = 0; i < ADC_NUM_CHANNELS; i++){
			int val;
			values[i].datum.i = 4095 - readADC(i);
			// printf("chan%d %d ", i, val);
		}

		OSC_resetBuffer(buf);
	
		if (OSC_openBundle(buf, OSCTT_Immediately())) {
		    complain("Problem opening bundle: %s\n", OSC_errorMessage);
		    return;
		}

		// arg.type = INT;
		// arg.datum.i = values[2];

	    WriteMessage(buf, "/adc", ADC_NUM_CHANNELS, values);

		if (OSC_closeBundle(buf)) {
		    complain("Problem closing bundle: %s\n", OSC_errorMessage);
		    return;
		}

	    SendBuffer(htmsocket, buf);
		// printf("\n");
		delay(5);
	}
}