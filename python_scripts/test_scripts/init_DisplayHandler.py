#!/usr/bin/env python

# Stellt innerhalb eines interaktiven python-Fensters die Instanz "lcd"
# der Klasse DisplayHandler bereit. 
# Aufrufen mit: exec(open("init_DisplayHandler.py").read())
# danach koennen alle Befehle interaktiv getestet werden.


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

	# Pins LCD
	DISPLAY_BL_PIN = pins['DISPLAY_BL_PIN']
	DISPLAY_SI     = pins['DISPLAY_SI']
	DISPLAY_CLK    = pins['DISPLAY_CLK']
	DISPLAY_RS     = pins['DISPLAY_RS']
	DISPLAY_CSB    = pins['DISPLAY_CSB']

	LED_ACTION_PIN = pins['LED_ACTION_PIN']
	SHUTDOWN_PIN = pins['SHUTDOWN_PIN']



# dogmlcd von hier: https://github.com/Gadgetoid/DogLCD, danach aber modifiziert. 
import DisplayHandler
import doglcd

import RPi.GPIO as GPIO
# __init__(self, lcdSI, lcdCLK, lcdRS, lcdCSB, pin_reset, pin_backlight):



lcd = DisplayHandler.DisplayHandler(DISPLAY_SI,DISPLAY_CLK,DISPLAY_RS,DISPLAY_CSB,-1,DISPLAY_BL_PIN,str(path_basesettings))
lcd.begin(doglcd.DOG_LCD_M163, 0x28)



info =     {'volume'       : 33,
            'playlist'     : '',          # Playlistname
            'state'    : 'play',          # stop, pause, play
            'song_number'  : '7',
            'elapsed_time' : 123,
            'title'        : '0123456789AB',
            'len_playlist' : '8'            # Anzahl der Titel in der Playlist fuer zyklisches Verhalten bei NEXT
            }  
info1 =     {'volume'       : 34,
            'playlist'     : '',          # Playlistname
            'state'    : 'play',          # stop, pause, play
            'song_number'  : '8',
            'elapsed_time' : 124,
            'title'        : '01_Name der Playliste_sehr_lang',
            'len_playlist' : '8'            # Anzahl der Titel in der Playlist fuer zyklisches Verhalten bei NEXT
            }  

uid0 = "123456789123"
uid1 = "undef"

string_short = "Felix der Hase"
string_middle = "Pippi Langstrumpf rauemt auf"
string_long = "Der PApanascht von der schokolade und wird dabei von den Kindern erwischt, DIeser stirngs ist sooo lang, dass..."
