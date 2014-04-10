import spidev    # import the spidev module
import time
import OSC

numChannels = 8;
lastValue = [-1, -1, -1, -1, -1, -1, -1, -1]
sampleTimePerChannel = 0.0026 # in s @ 0.5Mhz SPI Clock
sampleRate = 200 # in Hz
delay = (1.0/sampleRate) - (sampleTimePerChannel * numChannels)

spi = spidev.SpiDev()   # create a new spidev object
spi.open(0, 1)          # open bus 0, chip enable 1
spi.max_speed_hz = 500000 # 1MHz

sc = OSC.OSCClient()
# sc.connect(('127.0.0.1', 57120)) #send locally to sc
sc.connect(('192.168.1.35', 57120)) #send to external sc

def sendOSC(name, val):
  msg = OSC.OSCMessage()
  msg.setAddress(name)
  msg.append(val)
  try:
    sc.send(msg)
  except:
    1+1 # dummy
  #print msg

def readADC(channel):
  if channel > 7 or channel < 0:
    return -1

  input_mode = 1; # single ended = 1, differential = 0
  command = 0x04; # start flag
  command |= (input_mode<<1);
  command |= (channel>>2) & 0x01; # add msb of channel in our first command byte
  bytes = spi.xfer2([command, channel<<6, 0x00])
  result = (bytes[1] & 0x0f)<<8 | bytes[2]
  return result;


try:
  while True:
    for channel in range(numChannels):
        value = readADC(channel)
        if value != lastValue[channel]:
          mappedValue = 1 - (value/4095.0)
          sendOSC("/adc"+str(channel), mappedValue)
        lastValue[channel] = value
        # print "%4d" % value,
    time.sleep(0.001)
    # print;
except KeyboardInterrupt:
  # Ctrl+C pressed, so...
  spi.close()
