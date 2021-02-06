#!/usr/bin/env python
# -*- coding: utf8 -*-

# Displayansteuerung des DOGM-LCD, angepasst auf die Anforderungen
# der zentralen Steuerung durch die StateMachine. 

# folgende Methoden der Basisklasse werden benutzt:
# - clear()
# - setCursor(Spalte, Zeile)
# - write("string")
#  

# sehr spezielle Klasse fuer folgende Display-Aufteilung eines 1602-Displays: 
# normaler Betrieb: (Musik abspielen)
# Feldnummer: 1_2_3_4_5_6_7_8_
# Zeile 0/1:    Titel_PL_in_Lauf            Titel der Playliste in Laufschrift? Oder Titel Song und Title Playliste in Laufschrift?
# Zeile 2:    01_S_02:51__100%            Songnummer,Leerzeichen, ElapsedTime als 'MM:SS', 2xLeerzeichen, Lautstaerke in %



import re
from Laufschrift import Laufschrift
import time
import hjson
import doglcd
import math


# Positionsnummern der Elemente, entsprechend obigem Entwurf.
COL_TITLE_NUM = 0
COL_STATUS = 3
COL_TIME = 5
COL_VOLUME = 12
LINE_INFO = 2

symbols = [ [0,10,10,10,10,10,10,0],            # Symbol "Pause"
            [0,0,15,15,15,15,15,0],             # Symbol "STOP"
            [0,8,12,14,15,14,12,8],             # play-Pfeil
            [0,4,10,18,20,18,20,0],            # Darstellung des "ß"
            [0,4,14,21,4,4,4,0],               # Pfeil hoch
            [0,4,4,4,21,14,4,0],               # Pfeil runter
            [31]*8,                            # Curser-Zeichen, chr(6)
            [31,17,27,21,21,27,17,31]]         # delete Zeichen  chr(7)

state_dict = {'pause':0, 'stop':1, 'play':2,'notavail':1 }

# Ersetzungsoperationen fuer den Songtitel
# Symbole sind teilweise schon im DOGM definiert!
REPLACE_DICT = {'Ä':chr(0x8E),
                'Ü':chr(0x9A),
                'Ö':chr(0x99),
                'ä':chr(0x84),
                'ü':chr(0x81),
                'ö':chr(0x94),
                'ß':chr(3),
                '-':chr(0x2D),
                '_':' '}

class DisplayHandler(doglcd.DogLCD):
    # von der Basisklasse werden folgende Methoden verwendet bzw. erwartet:
    # - clear()
    # - setCursor(Spalte, Zeile)
    # - write("string")
    # und __init__
    def __init__(self, lcdSI, lcdCLK, lcdRS, lcdCSB, pin_reset, pin_backlight, setupfile):
        # Initialisieren der Bsisklasse
        super().__init__(lcdSI, lcdCLK, lcdRS, lcdCSB, pin_reset, pin_backlight)

        # weitere Initialisierungen
        with open(setupfile,'r') as fobj:
            temp_dict = hjson.load(fobj)
            cfg_gl = temp_dict['global']                              # globale Einstellungen fuer alle Klassen
            cfg = temp_dict['DisplayHandler']
        
        self.lw = cfg['line_width']      # Breite der Zeilen
        self.ln = cfg['line_number']     # Anzahl der Zeilen

        # einzeilige Laufschriften
        self.ls = [Laufschrift(self.lw, os_front=cfg['os_front'],os_back=cfg['os_back'], format=cfg['format_ls']) for i in range(self.ln)]
        # zweizeilige Laufschriften
        self.ls.append(Laufschrift(2*self.lw, os_front=cfg['os_front'],os_back=cfg['os_back'], format=cfg['format_ls']))
        self.ls.append(Laufschrift(2*self.lw, os_front=cfg['os_front'],os_back=cfg['os_back'], format=cfg['format_ls']))
        # dreizeilige Laufschrift
        self.ls.append(Laufschrift(3*self.lw, os_front=cfg['os_front'],os_back=cfg['os_back'], format=cfg['format_ls']))
        self.ls_active = 0      # bitcodiert, 0 bis 63, welche Zeilen bei Laufschriftaktualisierung geschrieben werden sollen
        self.ls_blink = 0       # bitcodiert, 0 bis 8, welche Zeilen bei Laufschriftaktualisierung blinken sollen
        self.title = ''

        # Statzeile des jeweiligen Laufschritobjektes. Erst die einzeiligen, dann die zweizeiligen, dann das dreizeilige
        self.ls_startlines = [0,1,2,0,1,0]



    def write_info(self, info):
        # default mpd-Informationen waehrend normaler Musikwiedergabe
        self._write_title(info['title'])
        
        # Zeile mit der Datenanzeige: 
        self._write_title_num(info['song_number'])
        self._write_state(info['state'])
        self.write_time(info['elapsed_time'])
        self._write_volume(info['volume_disp'])


    def update_ls(self):
        # zu blinkende Zeilen loeschen
        for i in [0,1,2]:
            if self.ls_blink & (1<<i):
                self.setCursor(0,i)                
                self.write(" "*16)

        # "blinken" realisieren
        time.sleep(0.1)

        # jede aktivierte Laufschriftzeile schreiben und weiterruecken 
        for i,value in enumerate(self.ls):
            self.setCursor(0,self.ls_startlines[i])                
            if self.ls_active & (1<<i):
                self.write(value.stepget())

            # TODO: noch sehr buggy hier: Zeilenblinken geht von 0 bis 2, 
            # # Nummerierun g der Laufschrift komplizierter-...    
            elif self.ls_blink & (1<<i):
                # nur wenn nach Blinken notwendig ist, neu schreiben
                self.write(value.get())

    def write_single_line(self, data, start_line, blink=0, ls=True):
        # Spezialfall einer Einzelzeile

        # keine Laufschrift gewuenscht --> text einfach einkuerzen!
        if (ls!=True) and len(data)>self.lw:
            data=data[0:self.lw-1]
            
        self.write_lines(data, start_line, num_lines=1, blink=blink)


    def write_lines(self, data, start_line, num_lines=1, blink=0):
        # Einzelzeile schreiben, wenn zu kurz mit Leerzeichen auffuellen,
        # wenn zu lang als Laufschrift schreiben
        if blink: 
            self.ls_blink = self.ls_blink|(1<<start_line)
        else: 
            self.ls_blink = (self.ls_blink^(1<<start_line))&self.ls_blink

        # Sonderzeichen umwandeln
        data = self._clear_sonderzeichen(data)

        if num_lines == 1:
            self.ls[start_line].setbase(data) 
            self.ls_active = self.ls_active | (1<<start_line)
            # TODO: andere Laufschriften deaktivieren!
            if start_line == 0:
                self.ls_active = self.ls_active & ~8
            else:
                self.ls_active = self.ls_active & ~16

            self.ls_active = self.ls_active & ~(32)     # dreizeilige Laufschrift deaktivieren

        elif (num_lines == 2) and (start_line < self.ln):
            self.ls[start_line+self.ln].setbase(data) 
            self.ls_active = self.ls_active | (1<<(start_line+self.ln))
            # inaktiv setzen
            self.ls_active = self.ls_active & ~(1<<(start_line))
            self.ls_active = self.ls_active & ~(1<<(start_line+1))
            self.ls_active = self.ls_active & ~(32)     # dreizeilige Laufschrift deaktivieren
        elif (num_lines == 3) and (start_line==0):
            self.ls[5].setbase(data) 
            self.ls_active = 32
        else:
            print("DisplayHandler: Input")

        # Zeile tatsaechlich schreiben
        self.setCursor(0,start_line)
        if num_lines == 1:
            self.write(self.ls[start_line].get())
        elif (num_lines == 2) and (start_line < self.ln):
            self.write(self.ls[start_line+self.ln].get())
        elif (num_lines == 3) and (start_line==0):
            self.write(self.ls[5].get())

    def clear_line(self,start_line):
        # entsprechende Zeile mit Leerzeichen ueberschreiben, aus der Laufschriftverwaltung 
        # entfernen
        self.setCursor(0,start_line) 
        self.write(' '*self.lw)
        self.ls_active = self.ls_active & ~(1<<start_line)

    def write_uid(self, uid, start_line):
        # korrekte Formattierung der 12-Stelligen UID
        # xxx.xxx.xxx.xxx oder: "undef"
        # zum besseren Debuggen falls uid ein String --> direkt in der Zeile schreiben

        if isinstance(int(uid),int) and len(uid)==12:
            self.setCursor(0,start_line)
            self.write(uid[0:3]+'.'+uid[3:6]+'.'+uid[6:9]+'.'+uid[9:12])
        elif isinstance(uid,str):
            self.write_single_line("error: "+ uid, start_line)
        else:
            self.write_single_line("error: with uid???", start_line)


    def write_curval(self,data,start_line):
        # Aktuellen Wert und naechste Optionen fuer einen auswahlbaren
        # Einstellwert anzeigen:
        # "xxxx [yyyy] zzzz"
        self.setCursor(0,start_line)
        if len(data)==3:
            self.write(f'{data[0]:<4s} [{data[1]:^4s}] {data[2]:>4s}')  
        else:
            self.write("error: Datenlaenge")

            
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++  
# interne Teilfunktionen
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++  
    def _write_title(self, data):
        # bei neuen titeln diesen auf schoen beschneiden und die Laufschrift anpassen
        if self.title != data:

            self.title = data
            # Nummerieung entfernen, Umlaute entfernen
            temp_title = self._cleartitle()

            # Aufteilung in die zwei obrsten Zeilen erzeugen, 
            self.write_lines(temp_title, 0, 2)
        else:
            # Laufschrift aktualisieren
            self.update_ls()   

    def _cleartitle(self):
        # vom Titel die fuehrende Nummerierung entfernen, Leerzeichen einfuegen und das Ergebnis zurueckgeben
        temp_title = re.sub(r"^\d*", "", self.title)   # fuehrende Ziffern entfernen 

        for key in REPLACE_DICT:
            temp_title = temp_title.replace(key, REPLACE_DICT[key])  
        return temp_title

    def _clear_sonderzeichen(self, text):
        # Zeichen fuer ß initialisieren
        self.createChar(3,symbols[3])

        # Symbole hier definieren, in self.__init__ erzeudgt das einen Fehler
        self.createChar(6,symbols[4])
        self.createChar(7,symbols[5])

        # Sonderzeichen Testeingabe
        self.createChar(4,symbols[6])   # Curser
        self.createChar(5,symbols[7])   # Zeichen loeschen


        # Sonderzeichen durch den passenden char ersetzen
        for key in REPLACE_DICT:
            text = text.replace(key, REPLACE_DICT[key])  
        return text        

    def _write_title_num(self,data):
        # Verarbeitung nur als Integer, um die Formatierung korrekt durchfuehren zu koennen
        # ausserdem gleich Feld fuer state mit dranhaengen
        self.setCursor(COL_TITLE_NUM, LINE_INFO)
        try: 
            data = int(data)
            self.write('{:02d}'.format(data)+' '+chr(0))
        except ValueError:
            self.write(data[0:2]+' '+chr(0))

    def _write_state(self, data):
        # Zeichen nicht schreiben, sondernden Platzhalter aktualisieren?

        self.createChar(0, symbols[state_dict[data]])
            

    def write_time(self, data):
        # nur die verstrichene Zeit des Titels, Vorgabe als String moeglich
        # whitespace neben der Zeit auch ueberschreiben
        try:
            sec_played = int(float(data))     # verstrichene Geamtzeit des titels sekunden
        except TypeError:
            sec_played = 0
            logger.exception("quatsch bei der Uebergabe von time")
                
        #  verstrichene Geamtzeit in min:sec umrechnen
        min_played = sec_played // 60
        sec_played = sec_played % 60 

        self.setCursor(COL_TIME, LINE_INFO)
        self.write('{:02d}:{:02d}'.format(min_played,sec_played))

    def _write_volume(self,data):
        # Zahlenwert der Lautstaerke
        self.setCursor(COL_VOLUME, LINE_INFO)
        self.write('{:3d}%'.format(data)) 

    def clear_data(self):
        # interner Speicher zuruecksetzen, um neue Displaydarstellung
        # zu erzwingen, TODO: hier muss mal die Playlist rein
        self.title = ""
        self.ls_active = 0




        


        


if __name__ == "__main__":

    from pinbelegung_testscripts import *
    import time

    lcd = DisplayHandler(DISPLAY_SI,DISPLAY_CLK,DISPLAY_RS,DISPLAY_CSB,-1,DISPLAY_BL_PIN,'/home/dietpi/settings_and_data/base_settings.ini')
    lcd.begin(doglcd.DOG_LCD_M163, 0x28)

    lcd.clear()
    lcd.home()
    lcd.write("test")

    info0 =     {'volume'       : 33,
                'playlist'     : '',          # Playlistname
                'state'    : 'play',          # stop, pause, play
                'song_number'  : 7,
                'elapsed_time' : 123,
                'title'        : '01_Felix_in_Afrika_mit sehr_langem Titel und Laufschrift',
                'len_playlist' : 8            # Anzahl der Titel in der Playlist fuer zyklisches Verhalten bei NEXT
                }  
    info1 =     {'volume'       : 34,
                'playlist'     : '',          # Playlistname
                'state'    : 'play',          # stop, pause, play
                'song_number'  : 6,
                'elapsed_time' : 123,
                'title'        : '02_Felix_in_Afrika_',
                'len_playlist' : 8            # Anzahl der Titel in der Playlist fuer zyklisches Verhalten bei NEXT
                }  
    info2 =     {'volume'       : 34,
                'playlist'     : '',          # Playlistname
                'state'    : 'play',          # stop, pause, play
                'song_number'  : 6,
                'elapsed_time' : 123,
                'title'        : '02_Felix_in_Afrika_zwo_zeilen_lang',
                'len_playlist' : 8            # Anzahl der Titel in der Playlist fuer zyklisches Verhalten bei NEXT
                }  
    lcd.write_info(info0)

    ii=0

    #  0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF
    a="Test mit 32 Zeichen fuer 2 Zeile"
    b="Test mit 48 Zeichen fuer 3 Zeile oder 2 Zeilen"
    c="Test mit 64 Zeichen fuer 4 Zeile oder 2 Zeilen im Wechsel oder "

    for text in a,b,c:
        lcd.clear()
        lcd.write_single_line(text, 0, 3)
        for i in range(60):
            lcd.update_ls()
            time.sleep(0.2)



