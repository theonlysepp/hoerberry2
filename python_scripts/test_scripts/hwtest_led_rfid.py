#!/usr/bin/env python
# -*- coding: utf8 -*-
'''
Testskript zum minimaltst, ob die Hardware korrekt funktioniert. 
Hier die LED fuer den RFID-Lesestatus

ausfuehren mit:   python3 hwtest_led_rfid.py

'''


import RPi.GPIO as GPIO
import os, time

# Pinbelegung in dieser zentralen Datei pflegen
from PinbelegungKinderMP3 import *              
GPIO.setmode(GPIO.BOARD)


# GPIO fuer die Ansteuerung aktivieren
GPIO.setup(LED_RFIDPIN, GPIO.OUT)

blink_time=1.0

try:
    for i in range(10):
        GPIO.output(LED_RFIDPIN, GPIO.HIGH)
        time.sleep(blink_time)
        GPIO.output(LED_RFIDPIN, GPIO.LOW)
        time.sleep(blink_time)
       
    # Aufraeumen am Schluss    
    GPIO.cleanup()
    
finally:
    # Aufraeumen am Schluss    
    GPIO.cleanup()    

