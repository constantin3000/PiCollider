#!/usr/bin/env python

import socket
import time
import sys
import spidev    
import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BCM)

# TCP PORT used : 54321
# inputs are mapped to pd "FUDI" messages of type [id value;]
# ie, value x prefixed by id (0-10), followed by semicolon:
# 0 x;  <==>  cv 1 (top left)
# 1 x;  <==>  cv 2 (bottom left)
# 2 x;  <==>  cv 3 (top centre)
# 3 x;  <==>  cv 4 (bottom centre)
# 4 x;  <==>  cv 5 (top right)
# 5 x;  <==>  cv 6 (bottom right)
# 6 x;  <==>  trigger 1
# 7 x;  <==>  trigger 2
# 8 x;  <==>  trigger 3
# 9 x;  <==>  button 1
# 10 x; <==>  button 2


# TCP:
TCP_IP = '127.0.0.1'
TCP_PORT = 54321
BUFFER_SIZE = 1024
CONTROL_RATE = 0.001 # seconds

# SPI:

spi = spidev.SpiDev()   # new spidev object
spi.open(0, 1)          # open bus 0, chip enable 1

# GPIO:

GPIO.setup(22, GPIO.IN) # trig input 1 
GPIO.setup(24, GPIO.IN) # trig input 2 
GPIO.setup(23, GPIO.IN) # trig input 3 
# GPIO.setup(14, GPIO.IN) # button 1
GPIO.setup(3,  GPIO.IN) # button 2 

# ISRs:
# really, you'd want to send a "bang" here but i haven't figured out the FUDI message
# doesn't seem to be a terribly well documented format.

TR1 = 6  # trigger 1
TR2 = 7  # trigger 2
TR3 = 8  # trigger 3
B1  = 9  # button 1
B2  = 10 # button 2

def trigger1(channel):
	print "trigger 1 detected\n" 
	x = 1
	message_string = ("%d %d;") % (TR1, x)  # mapped to 6 x;
	s.send(message_string)
	

def trigger2(channel):
	print "trigger 2 detected\n" 
	x = 1
	message_string = ("%d %d;") % (TR2, x)  # mapped to 7 x;
	s.send(message_string)
	

def trigger3(channel):
	print "trigger 3 detected\n" 
	x = 1
	message_string = ("%d %d;") % (TR3, x)  # mapped to 8 x;
	s.send(message_string)

def button1(channel):
	print "top button pressed\n"
	x = 1
	message_string = ("%d %d;") % (B1, x)   # mapped to 9 x;
	s.send(message_string)

def button2(channel):
	print "lower button pressed\n"
	x = 1
	message_string = ("%d %d;") % (B2, x)   # mapped to 10 x;
	s.send(message_string)

GPIO.add_event_detect(22, GPIO.FALLING, callback=trigger1)
GPIO.add_event_detect(24, GPIO.FALLING, callback=trigger2)
GPIO.add_event_detect(23, GPIO.FALLING, callback=trigger3)
# GPIO.add_event_detect(14, GPIO.FALLING, callback=button1)
GPIO.add_event_detect(3,  GPIO.FALLING, callback=button2)

# ADC :

def readADC(channel):

    # spi.xfer2 : send three bytes / return three bytes:
    cmd = 6  			   	 	 # single ended operation
    cmd = cmd + (channel >> 2)    		 # channel MSBit
    r = spi.xfer2([cmd, channel << 6, 0])	 # == [command byte, channel select, don't care]
    v = ((r[1] & 15) << 8) + r[2] 		 # Byte 2 (MSB) + Byte 3 (LSB) 
    return v;

# open TCP connection to pd

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    # s.connect((TCP_IP, TCP_PORT))
    print ("connected: port %d") % (TCP_PORT)  

except socket.error as err:
    # Exit on error
    print "could not connect . . . aborting.\nError: %s" % (err)
    sys.exit(1)


while True:
    try:
        # read the six ADC channels
        for x in range(2, 8):
		# invert value // TD: some averaging
	    	y = (4095 - readADC(x))>>2
	    	# format FUDI messages : id value semicolon
	    	message_string = ("%d %d;") % (7-x, y)
	    	print "%4d (ch %d)" % (y, 7-x),	
	    	# s.send(message_string)			
      	    	time.sleep (CONTROL_RATE)
	print
       
        
    except KeyboardInterrupt:
        # CTRL + C 
        time.sleep(0.2)
	GPIO.cleanup()       # clean up GPIO on CTRL+C exit 
        print "Closing connection"
        s.close()
        break
try:
    s.close()
except:
    pass
