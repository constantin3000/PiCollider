import numpy
import spidev    # import the spidev module
import time
import OSC

numChannels = 6;
channelOffset = 2;
numSamples = 4;

# values = numpy.empty((numChannels, numSamples), dtype=numpy.uint16)
sampleIndex = 0
values = [-1, -1, -1, -1, -1, -1]
# lastValues = [-1, -1, -1, -1, -1, -1, -1, -1]

spi = spidev.SpiDev()   # create a new spidev object
spi.open(0, 1)          # open bus 0, chip enable 1
spi.max_speed_hz = 500000 # 1MHz

sc = OSC.OSCClient()
sc.connect(('127.0.0.1', 57120)) #send locally to sc
# sc.connect(('192.168.1.35', 57120)) #send to external sc

def init():
  values = values * 0
  lastSendValue = lastSensValue * 0

def sendOSC(_name, _values):
  msg = OSC.OSCMessage()
  msg.setAddress(_name)
  for value in _values:
    msg.append(4095 - value)
  try:
    sc.send(msg)
  except:
    1+1 # dummy
  #print msg

def readADC(_channel):
  if _channel > 7 or _channel < 0:
    return -1

  input_mode = 1; # single ended = 1, differential = 0
  command = 0x04; # start flag
  command |= (input_mode<<1);
  command |= (_channel>>2) & 0x01; # add msb of channel in our first command byte
  bytes = spi.xfer2([command, _channel<<6, 0x00])
  result = (bytes[1] & 0x0f)<<8 | bytes[2]
  return result;

try:
  while True:
    for channel in range(numChannels):
      # values[channel, sampleIndex] = readADC(channel)
      values[channel] = readADC(channel + channelOffset)

    # medianValues = numpy.median(values, axis=1)
    # medianValues = 1 - (medianValues/4095.0)
        # print "%4d" % value,
    sendOSC("/adc", values)
    # sampleIndex += 1
    # sampleIndex %= numSamples

    time.sleep(0.05)
    # print;
except KeyboardInterrupt:
  # Ctrl+C pressed, so...
  spi.close()
