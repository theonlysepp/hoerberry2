#!/usr/bin/env python

# Stellt innerhalb eines interaktiven python-Fendters die Instanz "lcd"
# der Klasse doglcd.DogLCD bereit. 
# Aufrufen mit: exec(open("init_dogm163.py").read())

# Pinbelegung und Pfad zu den Modulen
from pinbelegung_testscripts import *

# dogmlcd von hier: https://github.com/Gadgetoid/DogLCD, danach aber modifiziert. 
import doglcd, datetime, time, threading

import RPi.GPIO as GPIO
# __init__(self, lcdSI, lcdCLK, lcdRS, lcdCSB, pin_reset, pin_backlight):





# mit backlight
# alte Belegung mit GPIO.setmode(GPIO-BMC)
#lcd = doglcd.DogLCD(10,11,25,8,-1,DISPLAY_BL_PIN)
# neue Belegung einheitlich mit GPIO.setmode(GPIO.BOARD)
lcd = doglcd.DogLCD(DISPLAY_SI,DISPLAY_CLK,DISPLAY_RS,DISPLAY_CSB,-1,DISPLAY_BL_PIN)

lcd.begin(doglcd.DOG_LCD_M163, 0x28)

# backlight setzen. 
lcd.clear()
lcd.home()

symbols = [ [0,10,10,10,10,10,10,0],    
            [0,0,15,15,15,15,15,0],   
            [0,8,12,14,15,14,12,8] ]