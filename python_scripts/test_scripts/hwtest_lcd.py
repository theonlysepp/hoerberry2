#!/usr/local/bin/python
# coding: UTF-8

import RPi.GPIO as GPIO
from RPLCD.i2c import CharLCD
import time


lcd = CharLCD(i2c_expander='PCF8574', address=0x27, port=1,   # i2c_expander: 'PCF8574', 'MCP23008' oder 'MCP23017'
cols=16, rows=2, dotsize=8,
charmap='A02',
auto_linebreaks=True,
backlight_enabled=True)

ii=0
sleeptime=0.05

lcd.write_string('01234567890123{:02d}'.format(ii))
lcd.write_string('ABCDEF67890123{:02d}'.format(ii))

# Test der Befehle
try:
    print('selektiv anpassen')
    while ii<30:
        ii+=1
        #lcd.clear()
        
        lcd.home()
        lcd.cursor_pos = (0,14)
        lcd.write_string('{:02d}'.format(ii))
        lcd.cursor_pos = (1,14)
        lcd.write_string('{:02d}'.format(ii))
        time.sleep(sleeptime)
        
    print('alles ueberschreiben')
    while True:
        ii+=1
        #lcd.clear()
        lcd.home()
        lcd.write_string('01234567890123{:02d}'.format(ii))
        lcd.write_string('ABCDEF67890123{:02d}'.format(ii))
        time.sleep(sleeptime)
finally:
    print('Stopping GPIO monitoring...')
    GPIO.cleanup()
    print('Program ended.')
