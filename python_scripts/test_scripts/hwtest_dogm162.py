#!/usr/bin/env python


# Pfad zu den Modulen hinzufuegen, sollten immer im uebergeordneten Verzeichnis liegen
# fuer den Import von Rot_ENC
from pathlib import Path
import sys
import hjson

# alle relevanten Pfade erzeugen
p_test_skripts=Path('.').absolute()
p_python = p_test_skripts.parent
p_github = p_python.parent
p_settings = Path(p_github, 'settings_and_data')

# Pfad fuer den Modulimport von doglcd hinzufuegen
sys.path.append(str(p_python))

# einmalig der allgemeine Ort von basesettings.ini,
path_basesettings = Path(p_settings,'base_settings.ini')

# Grundeinstellungen laden
with open(path_basesettings,'r') as fobj:
    temp_dict = hjson.load(fobj)
    settings_gl = temp_dict['global']

# Pinbelegung laden und in die Variablen schreiben
with open(settings_gl['fname_pinbelegung'],'r') as fobj:
	pins = hjson.load(fobj)   

	# Pins LCD
	DISPLAY_BL_PIN = pins['DISPLAY_BL_PIN']
	DISPLAY_SI     = pins['DISPLAY_SI']
	DISPLAY_CLK    = pins['DISPLAY_CLK']
	DISPLAY_RS     = pins['DISPLAY_RS']
	DISPLAY_CSB    = pins['DISPLAY_CSB']

	LED_ACTION_PIN = pins['LED_ACTION_PIN']
	SHUTDOWN_PIN = pins['SHUTDOWN_PIN']

# dogmlcd von hier: https://github.com/Gadgetoid/DogLCD, danach aber modifiziert. 
import doglcd, datetime, time, threading

import RPi.GPIO as GPIO
# __init__(self, lcdSI, lcdCLK, lcdRS, lcdCSB, pin_reset, pin_backlight):

# LED_ACTION (gruen) aktiv setzen
GPIO.setmode(GPIO.BOARD)
GPIO.setup(LED_ACTION_PIN, GPIO.OUT, initial=GPIO.HIGH)


# mit backlight
# alte Belegung mit GPIO.setmode(GPIO-BMC)
#lcd = doglcd.DogLCD(10,11,25,8,-1,DISPLAY_BL_PIN)
# neue Belegung einheitlich mit GPIO.setmode(GPIO.BOARD)
lcd = doglcd.DogLCD(DISPLAY_SI, DISPLAY_CLK, DISPLAY_RS, DISPLAY_CSB, -1, DISPLAY_BL_PIN)

lcd.begin(doglcd.DOG_LCD_M163, 0x28)

lcd.clear()


lcd.setBacklight(GPIO.HIGH,0)
time.sleep(1)
lcd.write("Test-String")
time.sleep(10)
lcd.clear()

