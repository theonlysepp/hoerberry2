#!/usr/local/bin/python
# coding: UTF-8

# Hier fuer alle Testskripte die aktuelle Pinbelegung laden. 
# Quelle ist die Json-Datei, die auch von der main.py geladen wird. 
# Die Variablen mit den Pinnummern sind dann in den Testdateien verfuegbar. 
# Einbinden mit "from pinbelegung_testscripts import *"

# Nummerierung ist immer: GPIO.setmode(GPIO.BOARD)



import hjson
# Pinbelegung laden
with open('/home/dietpi/user_data/pinbelegung.ini','r') as fobj:
     pins = hjson.load(fobj)   


LED_ACTION_PIN = pins['LED_ACTION_PIN']

BuNextPIN = pins['BuNextPIN'] 
BuPrevPIN = pins['BuPrevPIN']


VolumePIN_DT = pins['VolumePIN_DT']
VolumePIN_CLK = pins['VolumePIN_CLK']

PausePIN_SW = pins['PausePIN_SW']
PausePIN_DT = pins['PausePIN_DT']
PausePIN_CLK = pins['PausePIN_CLK']

SHUTDOWN_PIN = pins['SHUTDOWN_PIN']


# Pins LCD
DISPLAY_BL_PIN = pins['DISPLAY_BL_PIN']
DISPLAY_SI     = pins['DISPLAY_SI']
DISPLAY_CLK    = pins['DISPLAY_CLK']
DISPLAY_RS     = pins['DISPLAY_RS']
DISPLAY_CSB    = pins['DISPLAY_CSB']




# Pfad zu den Modulen hinzufuegen
import sys
sys.path.append('/home/dietpi/python_scripts')