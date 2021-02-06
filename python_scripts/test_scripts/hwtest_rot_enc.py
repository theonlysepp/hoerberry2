'''
Testskript zum minimaltst, ob die Hardware korrekt funktioniert. 
Hier die beiden KY-040 Drehencoder

ausfuehren mit:   python hwtest_ky040.py

Mit den Einstellungen wurde eine schnelle aber stabile Reaktion erreicht
ACHTUNG: modifizierte Klasse, bei der Anleitung darauf aufpassen!

'''

import RPi.GPIO as GPIO
from ROT_ENC import ROT_ENC
import os, time

# Pinbelegung laden
from pinbelegung_testscripts import *
# Pinbelegung gemaess Gesamtplan
GPIO.setmode(GPIO.BOARD)

# LED 
GPIO.setup(LED_ACTION_PIN, GPIO.OUT)

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

def LEDblink(pin):
    # LED fuer 3 ms
    GPIO.output(LED_ACTION_PIN, GPIO.HIGH)
    time.sleep(0.005)
    GPIO.output(LED_ACTION_PIN, GPIO.LOW)
 


GPIO.setmode(GPIO.BOARD)


# KyVol
volume = ROT_ENC(VolumePIN_CLK, VolumePIN_DT, drehVolume, 
                        debounce=15, debounce_extra=1, sleeptime=0.001)
volume.start()

# KyPause
pause = ROT_ENC(PausePIN_CLK, PausePIN_DT, drehPause, 
                        debounce=15, debounce_extra=1, sleeptime=0.001)
pause.start()



try:
    while True:
        time.sleep(10)
        print('Ten seconds...')

finally:
    volume.stop()
    pause.stop()
    GPIO.cleanup()
    print('Stopping GPIO monitoring...')
    GPIO.cleanup()
    print('Program ended.')