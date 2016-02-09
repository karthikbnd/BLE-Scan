#!/usr/bin/python
import RPi.GPIO as GPIO
import Adafruit_DHT
import time

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(17, GPIO.OUT)
#GPIO.setmode(GPIO.BOARD)

# Sensor Model DHT11 
SENSOR = Adafruit_DHT.DHT11 #.DHT22

# DHT Sensor PIN
PIN4 = 4 #dht pin
PIN17 = 17 #buzzer pin

# Min and Max Humidity
MAX_HUMI = 63
MIN_HUMI = 58

#Min and Max Temperature
MAX_TEMP = 30
MIN_TEMP = 25

# While
while True:
  try:
       humidity, temperature = Adafruit_DHT.read_retry(SENSOR, PIN4)
       print 'Temperature={0:0.1f}*C  Humidity={1:0.1f}%'.format(temperature, humidity)       
       #if humidity >= MAX_HUMI:
       if temperature >= MAX_TEMP:
               GPIO.output(17, True)
               print "Buzzer ON"
               time.sleep(5)
               
       #elif humidity <= MIN_HUMI:
       elif temperature < MAX_TEMP:
               GPIO.output(17, False)
               print "Buzzer  OFF"
               time.sleep(5)
  except KeyboardInterrupt:
		GPIO.cleanup()
		exit
