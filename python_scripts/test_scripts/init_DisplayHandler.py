#!/usr/bin/env python

# Stellt innerhalb eines interaktiven python-Fendters die Instanz "lcd"
# der Klasse DisplayHandler bereit. 
# Aufrufen mit: exec(open("init_DisplayHandler.py").read())

# Pinbelegung und Pfad zu den Modulen
from pinbelegung_testscripts import *

# dogmlcd von hier: https://github.com/Gadgetoid/DogLCD, danach aber modifiziert. 
import DisplayHandler
import doglcd

import RPi.GPIO as GPIO
# __init__(self, lcdSI, lcdCLK, lcdRS, lcdCSB, pin_reset, pin_backlight):



lcd = DisplayHandler.DisplayHandler(DISPLAY_SI,DISPLAY_CLK,DISPLAY_RS,DISPLAY_CSB,-1,DISPLAY_BL_PIN,'/home/dietpi/settings_and_data/base_settings.ini')
lcd.begin(doglcd.DOG_LCD_M163, 0x28)



info =     {'volume'       : 33,
            'playlist'     : '',          # Playlistname
            'state'    : 'play',          # stop, pause, play
            'song_number'  : 7,
            'elapsed_time' : 123,
            'title'        : '0123456789AB',
            'len_playlist' : 8            # Anzahl der Titel in der Playlist fuer zyklisches Verhalten bei NEXT
            }  
info1 =     {'volume'       : 34,
            'playlist'     : '',          # Playlistname
            'state'    : 'play',          # stop, pause, play
            'song_number'  : 8,
            'elapsed_time' : 124,
            'title'        : '01_Name der Playliste_sehr_lang',
            'len_playlist' : 8            # Anzahl der Titel in der Playlist fuer zyklisches Verhalten bei NEXT
            }  

uid0 = "123456789123"
uid1 = "undef"

string_short = "Felix der Hase"
string_middle = "Pippi Langstrumpf rauemt auf"
string_long = "Der PApanascht von der schokolade und wird dabei von den Kindern erwischt, DIeser stirngs ist sooo lang, dass..."
