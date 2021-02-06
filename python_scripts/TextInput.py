#!/usr/bin/env python
# -*- coding: utf8 -*-

# Klasse zum erstellen von Strings mit Digitaleingaben (Buttons), incl. Ausgabe an ein Display.

import string
import time

# spezielle Zeichendefinition fuer chr(4) und chr(5) in DisplyHandler!
# Platzhalter, dass hier kein Eintrag ist. Um den String wieder zu kuerzen.
emptychar = chr(5)
# Anzeige, dass sich hier der cursor befindet
cursorchar = chr(4)

# Verfuegbarer Zeichensatz, aus dem der String zusammengesetzt wird. 
# Sonderzeichen sind modifiziert, weil entweder nicht im Display darstellbar, oder extrem unwahrscheinlich für ein Passwort bzw. Wlan-name
charsets = ( string.digits, string.ascii_lowercase, string.ascii_uppercase, '!"#$%&\'()*+,-./:;<=>?[]_{|} ', emptychar)

displaymode_char = 0
displaymode_cursor = 1


class TextInput():

    def __init__(self, displaylen=16, display_currentpos=10, frequency=0.5):

        self.dl = displaylen
        self.d_cp = display_currentpos
        self.fr = frequency 
        self.timer = time.time()

        # default: zeitgesteuert zwischen Zeichen und Cursor wechseln
        self.displaymode = displaymode_char

        # current_charset, Nummer der fuer jedes Zeichen aktiven charsets
        self.cur_cs = [0]
        # charset_index, Indexnummer im current_charset fuer jedes Zeichen
        self.cs_i = [0]
        # aktueller Index im String
        self.cp = 0
        
        # Liste aller Zeichen
        self.str_list = [self._init_char()]



    def _init_char(self):
        # an einem neuen Cursorpunkt das erste Zeichen erzeugen
        # derzeit: '0'
        self.cur_cs.append(0)
        self.cs_i.append(0)
        return charsets[self.cur_cs[self.cp]][self.cs_i[self.cp]]

    def _cut_empty_string(self):
        # ganz rechts stehenden empty_string entfernen
        if emptychar in self.str_list:
            self.str_list = self.str_list[0:self.str_list.index(emptychar)]

    def _update_char(self):
        # den tatsaechlichen Eintrag an der aktuellen Cursorpositin un self.str_list aktualsieren
        self.str_list[self.cp] = charsets[self.cur_cs[self.cp]][self.cs_i[self.cp]]

    def cursor_left(self):
        # Curser erstmal wieder rausschmeissen und durch das entsprechende Zeichen ersetzen
        self._update_char()

        # cursor eine Position nach links verschieben
        self.cp = max(0, self.cp-1)

        # String kuerzen, wenn ganz rechts nur der Platzhalter steht
        self._cut_empty_string()
        self.displaymode = displaymode_cursor
        self.timer = time.time()


    def cursor_right(self):
        # Curser erstmal wieder rausschmeissen und durch das entsprechende Zeichen ersetzen
        self._update_char()

        if self.str_list[self.cp] == emptychar:
            # an der letzten Stelle erstmal Inhalt einfuegen, sonst wird der String nicht fortgesetzt
            return
        else:
            self.cp += 1
            # wir waren gerade ganz rechts, es muss ein weiteres Zeichen hinzugefügt werden
            if self.cp > (len(self.str_list)-1):
                
                self.str_list.append(self._init_char())
        self.displaymode = displaymode_cursor
        self.timer = time.time()

    def change_charset(self):
        # Nummer des ausgewaehlten Zeichensatzes inkrementieren, zyklisch
        # aktuelles Zeichen initialisiere

        self.cur_cs[self.cp] = (self.cur_cs[self.cp] + 1) % len(charsets)
        self.cs_i[self.cp] = 0
        self.displaymode = displaymode_char
        self.timer = time.time()

        # Eintrag in self.str_list aktualisieren
        self._update_char()

    def change_index(self, step):
        # ausgewahltes Zeichen inkrementieren, zyklisch
        self.cs_i[self.cp] = (self.cs_i[self.cp] + step) % len(charsets[self.cur_cs[self.cp]])
        self.displaymode = displaymode_char
        self.timer = time.time()

        # Eintrag in self.str_list aktualisieren
        self._update_char()

    def get_display_string(self):
        # displayausgabe zurueckgeben
        # - nur den darstellbaren Teil zurueckgeben, je nach Cursorposition und Displaybreite
        # - aktuelle Cursorposition zyklisch mit 

        if self.displaymode == displaymode_char:
            if time.time() - self.timer > self.fr:
                # nach abgelaufener Zeit die Cursorposition hervorheben
                self.timer = time.time()
                self.str_list[self.cp] = cursorchar
                self.displaymode = displaymode_cursor
            else:
                # korrektes Zeichen anzeigen
                self._update_char()

        else:
            if time.time() - self.timer  > self.fr:
                # nach abgelaufener Zeit das Zeichen anzeigen hervorheben
                self.timer = time.time()
                self._update_char()
                self.displaymode = displaymode_char
            else:
                # Cursorposition anzeigen
                self.str_list[self.cp] = cursorchar


        # Startwert passend waehlen
        if self.cp < self.d_cp:
            output = self.str_list
        else:
            output = self.str_list[(self.cp-self.d_cp):]

        # Stringlaenge auf DIsplaybreite beschneiden
        if len(output) > self.dl:
            output = output[0:self.dl-1]

        # Aus der Liste von Zeichen wird jetzt ein String
        output = ''.join(output)
        
        # Ausgabe mit Leerzeichen auffuellen bis zur vollen Displaybreite!
        return output.ljust(self.dl)
    
    def get_string(self):
        # tatsaechlich erzeugten string zurueckgeben

        # Inhalt an der Cursorposition aktualisieren
        self._update_char()

        self._cut_empty_string()

        return ''.join(self.str_list)

    def clear_all(self):
        # alles zuruecksetzen
        self.timer = time.time()

        # default: zeitgesteuert zwischen Zeichen und Cursor wechseln
        self.displaymode = displaymode_char

        # current_charset, Nummer der fuer jedes Zeichen aktiven charsets
        self.cur_cs = [0]
        # charset_index, Indexnummer im current_charset fuer jedes Zeichen
        self.cs_i = [0]
        # aktueller Index im String
        self.cp = 0
        
        # Liste aller Zeichen
        self.str_list = [self._init_char()]


if __name__ == "__main__":

    a = TextInput()

    a.cursor_right()        
    a.cursor_right()        
    a.cursor_right()

    print("?: 0000") 
    # print(a.get_string()       )

    # 00c0
    a.cursor_left()        
    a.change_charset()
    a.change_index(4)

    print("?: 00c0") 
   # print(a.get_string()       )

    # 02c0
    a.cursor_left()        
    a.change_index(4)
    print("?: 02c0") 
    print(a.str_list)
    # print(a.get_string()       )

    # E2c0
    a.cursor_left()
    a.change_charset()
    a.change_charset()
    a.change_index(1)
    a.change_index(1)
    a.change_index(1)
    a.change_index(1)

    print("?: E2c0") 
    print(a.get_string()       )    

    # Displaytest: Display mit Curser, Ausgabe immer ohne Curser
    # print("Display:")
    # for i in range(6):
    #     print(a.get_display_string())
    #     print(a.get_string()       )  
    #     time.sleep(0.4)


    # Platzhalter hinten
    for i in range(10):
        a.cursor_right()
    a.change_charset()
    a.change_charset()
    a.change_charset()
    a.change_charset()

    print("Platzhalter hinten angezeigt?")
    print(a.get_display_string())
    print(a.get_string())
    
    # Platzhalter entfernen
    a.cursor_left()
    print(a.get_display_string())




