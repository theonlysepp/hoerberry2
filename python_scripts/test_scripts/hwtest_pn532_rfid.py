#!/usr/bin/env python
# -*- coding: utf8 -*-
'''
Testskript zum minimaltst, ob die Hardware korrekt funktioniert. 
Hier der PN532 RFID-Reader mit I2C-Verbindung
Achtung: Dip-Schalter korrekt einstellen: Oben-Unten

ausfuehren mit:   python3 hwtest_pn523_rfid.py

'''

from pathlib import Path
import sys
import hjson

# alle relevanten Pfade erzeugen
p_test_skripts=Path('.').absolute()
p_python = p_test_skripts.parent

# Pfad fuer den Modulimport von ROT_ENC hinzufuegen
sys.path.append(str(p_python))



# wichtig: modifizierte Klasse nutzen!
from i2c_sc import *
from py532lib.frame import *
from py532lib.constants import *
import time
 
pn532 = Pn532_i2c()
pn532.SAMconfigure()


print('Test des RFID-Readers. Bitte Karte anhalten. Abbrechen mit STRG + C.')
print('Karten-IB wird angezeigt. Abbrechen mit STRG + C.')

try:
    while True:
        start_time = time.time()
        
        card_data = pn532.read_mifare()
        #print("time: ", time.time()-start_time)
        
        if isinstance(card_data, Pn532Frame):
            print(card_data.get_data())
        #else:
        #    print(card_data)
        time.sleep(2.0)
    
        
finally:
    # Keyboard interrupt abfangen, GPIO aufraumen...
    print('Stopping GPIO monitoring...')
    print('Program ended.')    
    