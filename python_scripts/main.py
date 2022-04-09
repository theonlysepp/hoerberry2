# -*- coding: utf8 -*-

# Hauptdatei, die beim Hohfahren des Pi automatisch ausgefuehrt wird.
# Enthaelt alle Initialisierungen und die Hauptschleife fuer den RFID-Reader
# und das Display
#
# Optionen:   python3 main.py loglevel
# folgende Level sind zulaessig: INFO; DEBUG; WARNING; ERROR

# Module importieren
from RPi import GPIO
from subprocess import call
from math import floor
import re
import time
import sys

import hjson

# einmalig der allgemeine Ort von basesettings.ini
# TOOD: relativer Pfad, bezogen auf den aktuellen Ort
path_basesettings = '/home/pi/hoerberry2/settings_and_data/base_settings.ini'

# Grundeinstellungen laden
with open(path_basesettings,'r') as fobj:
     temp_dict = hjson.load(fobj)
     settings_gl = temp_dict['global']

# Pinbelegung laden
with open(settings_gl['fname_pinbelegung'],'r') as fobj:
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

GPIO.setmode(GPIO.BOARD)


import logging
# Format des Dateinamens fuer das logging steckt hier drin
timestamp = time.strftime('%xH%HM%M')
timestamp = timestamp.replace('/','_')

from pathlib import Path

# leere alte logfiles und errorfiles loeschen
for fname in ['logfile', 'errorfile']:
     f_list = list(Path(settings_gl[fname]).glob('*.log'))
     [ i.unlink() for i in f_list if (i.stat().st_size == 0) ]



# logging und Fehlerausgabe aus den base_settings.ini oder mit Kommandozeilenargument:
# python3 main.py LOGLEVEL
# Achtung: wird ein Loglevel angegeben, werden alle Fehler auch automatisch an die Konsole geschickt! 
if len(sys.argv) > 1 and (sys.argv[1] in ['DEBUG', 'INFO', 'WARNING', 'ERROR']):
     # Angabe eine Loggerlevels ueber die Konsole:
     # Ausgage entsprechend des levels, logausgabe und Fehlerausgabe an die Konsole
     loglevel=sys.argv[1]    

     logging.basicConfig(level=loglevel,
               format='%(asctime)s : %(levelname)s : %(name)s : %(message)s')  
else:               
     # Logging und Fehlerausgabe entsprechen den base_settings
     loglevel=settings_gl['Logging_Level']     

     # mit oder ohne logfile
     if settings_gl['logfile'] != 'None':
          logfile = settings_gl['logfile']+'logfile_{}.log'.format(timestamp)
          logging.basicConfig(filename=logfile,level=loglevel,
               format='%(asctime)s : %(levelname)s : %(name)s : %(message)s')  
     else:
          logging.basicConfig(level=loglevel,
               format='%(asctime)s : %(levelname)s : %(name)s : %(message)s')  
     # Python-Fehler auch in die Datei schreiben: (der Fehler wird nach ganz oben geschrieben)
     # optional
     if settings_gl['errorfile'] != 'None':
          sys.stderr = open(settings_gl['errorfile']+'errorfile_{}.log'.format(timestamp), 'w')

logger = logging.getLogger(__name__)

print("Logger Level main: ", logger.getEffectiveLevel())



# Modul MPD-CLient
from StateMachine import StateMachine

# Rotary encoder
from ROT_ENC import ROT_ENC


#-------------------------------------------------------------------------------
# Hardware initialisieren
# Pinbelegung aus PinbelegungKinderMP3.py



# Display
from DisplayHandler import DisplayHandler
import doglcd
lcd = DisplayHandler(DISPLAY_SI,DISPLAY_CLK,DISPLAY_RS,DISPLAY_CSB,-1,DISPLAY_BL_PIN,
        path_basesettings)
lcd.begin(doglcd.DOG_LCD_M163, 0x28)


# RFID Reader
from i2c_sc import *
from py532lib.frame import *
from py532lib.constants import *
RFID_reader = Pn532_i2c()
RFID_reader.SAMconfigure()


# MPD-Client
# im Editiermenue starten, wenn beide Tasten gedrueckt sind (=False!)
sm = StateMachine(RFID_reader, lcd, [LED_ACTION_PIN,BuNextPIN,BuPrevPIN],
               path_basesettings )


# KyVol
volume = ROT_ENC(VolumePIN_CLK, VolumePIN_DT, sm.OnVolumeRotary, 
                    debounce=15, debounce_extra=1, sleeptime=0.001)
volume.start()
    

# KyPause
pause = ROT_ENC(PausePIN_CLK, PausePIN_DT, sm.OnPauseRotary, 
                    debounce=15, debounce_extra=1, sleeptime=0.001)
pause.start()

# PauseButton
GPIO.setup(PausePIN_SW,GPIO.IN)
try:
     GPIO.add_event_detect(PausePIN_SW, GPIO.FALLING, bouncetime=200)
     GPIO.add_event_callback(PausePIN_SW, sm.OnPauseButton)
except RuntimeError:
     logger.error('RuntimeError Button: PausePIN_SW')
     # todo: was machen wir denn dann? Neustart, nochmal versuchen?
     time.sleep(10)
     GPIO.add_event_detect(PausePIN_SW, GPIO.FALLING, bouncetime=200)
     GPIO.add_event_callback(PausePIN_SW, sm.OnPauseButton)

# Taste Shutdown indirekt, nicht der VolumePIN_SW, sondern der HIGH gesetzte GPIO der onoff-shim
GPIO.setup(SHUTDOWN_PIN,GPIO.IN)
try:
     GPIO.add_event_detect(SHUTDOWN_PIN, GPIO.FALLING, bouncetime=200)
     GPIO.add_event_callback(SHUTDOWN_PIN, sm.OnShutdownButton)
except RuntimeError:
     logger.error('RuntimeError Button: SHUTDOWN_PIN')
     # todo: was machen wir denn dann? Neustart, nochmal versuchen?
     time.sleep(10)
     GPIO.add_event_detect(SHUTDOWN_PIN, GPIO.FALLING, bouncetime=200)
     GPIO.add_event_callback(SHUTDOWN_PIN, sm.OnShutdownButton)


logger.info('Intialisierungen beendent')

#-------------------------------------------------------------------------------------------------------------
# Hauptschleife


while True:
     sm.ubi()



                       