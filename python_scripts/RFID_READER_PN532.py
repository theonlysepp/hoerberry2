#!/usr/local/bin/python
# coding: UTF-8
'''
RFID_READER_PN532 Python Class

kleine Klasse, um die vorhandenen Rueckgabe der Python -Bibliothek ein bisschen anders zu firmatieren. 
Ziel ist eine Ausgabe als 12-stellign String aus Ziffern. 

'''

from i2c_sc import *
from py532lib.frame import *
from py532lib.constants import *

class RFID_READER_PN532:

    def __init__(self):
        self.pn532 = Pn532_i2c()
        self.pn532.SAMconfigure()
        self.ba = bytearray(b'0')
    
    def readID(self):
        # gucken, ob eine Karte da ist. Wenn ja, die UID als int zurueckgeben.
        # Wenn nicht, False
        card_data = self.pn532.read_mifare()

        if isinstance(card_data, Pn532Frame):
            self.ba = card_data.get_data()

            temp_uid = int.from_bytes(self.ba[6:], byteorder='little')
            return str(temp_uid)[0:12]

        else:
            return False

#test
if __name__ == "__main__":
    from time import sleep

    reader = RFID_READER_PN532()    

    try:
        while True:
            sleep(0.1)
            uid = reader.readID()
            if uid:
                print(uid)
    finally:
        print('Program ended.')
