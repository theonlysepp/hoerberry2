#!/usr/bin/env python

# Vorlage fuer die Einbindung in die Hoerberry-Software. 
# Ausserdem Test fuer die Hardware. 

import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
import time

reader = SimpleMFRC522()


try:
    while True:
        # Versuch, eine ID auszulesen.
        # Wenn keine Karte erkannt wird, gibt es NONE
        # Karte erkannt: ID als 12-stelligr Integer
        id = reader.read_id_no_block()
        if id:
           print(id)
        else:
            print('None')
        # 1 Sekunde warten
        time.sleep(1.0)
        
finally:
    # Keyboard interrupt abfangen, GPIO aufraumen...
    print('Stopping GPIO monitoring...')
    GPIO.cleanup()
    print('Program ended.')    
    
