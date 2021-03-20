#!/usr/local/bin/python
# coding: UTF-8

# Testablauf zum Ueberpruefen, ob die Hardware korrekt verbunden ist und funktioniert
# 
# Fuer die Knoepfe BuNext und BuPrev
# 
# Verkabelung gemaeß allgemeiner Pinbelegung:
# - Ein Tasterpin zum GPIO-PIN
# - EIn Tasterpin zum GND
# Der Eingangs-GPIO liegt normalerweise auf 3.3V, durch Tastendruck wird er auf GND runtergezogen
# 
# Mit der Einstellung und den vandalismustatern erfolgreich getestet. 
# Prellen nur bei langem Tastendruck, dann aber in der SW keine "Reaktion"


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

# Pfad fuer den Modulimport von ROT_ENC hinzufuegen
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
 
    BuNextPIN = pins['BuNextPIN'] 
    BuPrevPIN = pins['BuPrevPIN']

    VolumePIN_DT = pins['VolumePIN_DT']
    VolumePIN_CLK = pins['VolumePIN_CLK']

    PausePIN_SW = pins['PausePIN_SW']
    PausePIN_DT = pins['PausePIN_DT']
    PausePIN_CLK = pins['PausePIN_CLK']

    SHUTDOWN_PIN = pins['SHUTDOWN_PIN']


import RPi.GPIO as GPIO
from ROT_ENC import ROT_ENC
import os, time



# Pinbelegung gemaess Gesamtplan
GPIO.setmode(GPIO.BOARD)


# allgemeine Testparameter
bt = 20        # bouncetime in ms, kein neues Ausloesen des calbacks inerhalb der Zeit
bt_sc = 0.005  # softwaredebounce von mir: solange muss der Eingang stabil anliegen, in Sekunden 


def buttoncallback(channel, message):
    # allgemeie Reaktionsfunktion
    time.sleep(bt_sc)
    if GPIO.input(channel)==GPIO.LOW:
        print('channel: {:}'.format(channel) )
        print('Button {} pressed'.format(message))
    else:
        print('prelllllllen Button {}'.format(message))


def drehVolume(pin, direction):
    
    print("DrehVolume pin {}".format(pin))
    print("DrehVolume {}".format(direction))

        
def pressedVolume(pin):
     print("DrehVolume pressed")
     
def drehPause(pin, direction):
    print("DrehPause pin {}".format(pin))
    print("DrehPause {}".format(direction))
        
def pressedPause(pin):
     print("DrehPause pressed") 


# Beide Knoepfe sollen gleich reagieren
def BuNextPressed(channel):
    buttoncallback(channel, "Next")


def BuPrevPressed(channel):
    buttoncallback(channel,"Prev")

def PausePressed(channel):
    buttoncallback(channel,"Pause")

def VolumePressed(channel):
    buttoncallback(channel,"Volume")   

# BuNext
GPIO.setup(BuNextPIN,GPIO.IN)
GPIO.add_event_detect(BuNextPIN,GPIO.FALLING,callback=BuNextPressed,bouncetime=bt)

#BuPrev
GPIO.setup(BuPrevPIN,GPIO.IN)
GPIO.add_event_detect(BuPrevPIN,GPIO.FALLING,callback=BuPrevPressed,bouncetime=bt)

# Pause, Knopfdruck
GPIO.setup(PausePIN_SW,GPIO.IN)
GPIO.add_event_detect(PausePIN_SW,GPIO.FALLING,callback=PausePressed,bouncetime=bt)

# Volume, Knopfdruck
GPIO.setup(SHUTDOWN_PIN,GPIO.IN)
GPIO.add_event_detect(SHUTDOWN_PIN,GPIO.FALLING,callback=VolumePressed,bouncetime=bt)


# Drehgeber
# KyVol
volume = ROT_ENC(VolumePIN_CLK, VolumePIN_DT, drehVolume, 
                        debounce=15, debounce_extra=1, sleeptime=0.001)
volume.start()

# KyPause
pause = ROT_ENC(PausePIN_CLK, PausePIN_DT, drehPause, 
                        debounce=15, debounce_extra=1, sleeptime=0.001)
pause.start()


print('Test fuer die Platine Buttons:')
print('Tasten PREV und NEXT und PAUSE')
print('Drehgeber PAUSE und VOLUME')


try:
    while True:
        time.sleep(10)
        print('Ten seconds...')
finally:
    volume.stop()
    pause.stop()
    print('Stopping GPIO monitoring...')
    GPIO.cleanup()
    print('Program ended.')

