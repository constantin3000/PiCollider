#!/usr/bin/python

# Lots of Pots Board Analog to Digital Converter test
# Modern Device
# www.moderndevice.com

import spidev    # import the spidev module
import time      # import time for the sleep function

spi = spidev.SpiDev()   # create a new spidev object
spi.open(0, 1)          # open bus 0, chip enable 0

def readadc(channel):
  if channel > 7 or channel < 0:
    return -1

  input_mode = 1; # single ended = 1, differential = 0
  command = 0x04; # start flag
  command |= (input_mode<<1);
  command |= (channel>>2) & 0x01; # add msb of channel in our first command byte
  bytes = spi.xfer2([command, channel<<6, 0x00])

  result = (bytes[1] & 0x0f)<<8 | bytes[2]

  return result;

while True:
    for i in range(8):
        value = readadc(i)
        print "%4d" % value,
    time.sleep(0.2)
    print;
