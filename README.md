PiCollider
==========

Supercollider on RaspberryPi


some quick n dirty code bits to run Supercollider on the RaspberryPi using [a pcb by mxmxmx](http://www.muffwiggler.com/forum/viewtopic.php?t=104896&postdays=0&postorder=asc&start=0) (thanks!)
the PCB provides a MCP3208 12 bit ADC for pots and CV inputs and a PCM 5102 DAC for audio output in a very nice and compact form factor.

Overall performance with the RasPi running at 1000Mhz is decent and there is some latency. Still needs some work as the osc message handling is a bit too expensive and dumb (could be event based or something).
Latency probably comes from jackd running in dummy mode as the i2s driver apparently doesn't support mmap and you have to route it to alsa_out (whole routing seems expensive aswell :( ). Everything is running on the RasPi with Raspian and SC3.7

```
adc2osc.c - c code for adc sampling and sending out osc bundles
adc2osc_bundle.py - python script for adc sampling and sending out osc bundles (slow)
PulsarOsc.scd - simple Pulsarsynthesis SC Patch
start.sc - simple sc startupscipt 
````


to get everything running you need to compile SC 3.7, see Frederik Olofssons [very helpful tutorial](http://supercollider.github.io/development/building-raspberrypi.html)

compile adc2osc.c, beforhand you need to install the [wiringPi Libraries](http://wiringpi.com/)
```
gcc adc2osc.c osc/htmsocket.c osc/OSC-client.c osc/OSC-timetag.c -lwiringPi -o adc2osc
```
after that you need to start jackd in dummy mode, see [Sam Aarons tutorial](http://sam.aaron.name/2012/11/02/supercollider-on-pi.html) for reference
```
jackd -P80 -m -p 32 -d dummy -p 256 -r48000 &
```
start alsa_out with quality 1, dump error messages and standart output (2>&1 > /dev/null), PCM5102 is configured as our default system soundcard
```
alsa_out -q1 -p256 2>&1 > /dev/null &
```
start scsynth
```
scsynth -u 57110 &
```
connect outputs
```
jack_connect SuperCollider:out_1 alsa_out:playback_1 &
jack_connect SuperCollider:out_2 alsa_out:playback_2 &
```
now run the adc osc bridge, -h argument is the host (you can also send it to your computer for testing), -d is the delay time in ms between adc readout
```
adc2osc -h 127.0.0.1 57120 -d 20 &
```

and finally sclang
```
sclang PulsarOsc.scd
```
