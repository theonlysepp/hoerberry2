#!/usr/bin/env python
# -*- coding: utf8 -*-

# zentrale Klasse des Hoerberry2:
# - Zutandsautomat
# - Befehle und Statusabfragen des MPDClient
# - alle Tasteninterationnen hier verarbeiten
# - Display-inhale schreiben

# Liste komplett? 
# Weitere Zustaende...
# debuggen


import RPi.GPIO as GPIO

import mpd
import subprocess

import os
import shutil    # kopieren von Dateien

from pathlib import Path

import sys
import copy
from random import shuffle, randint
from datetime import date

# from math import floor
# import re
import time
import hjson

import logging
import traceback

# wlan und intenet
import socket

# meine Klassen
from RFID_READER_PN532 import RFID_READER_PN532
from time_manager import TimeManager
from TextInput import TextInput
   

def read_playlists(path):
    # anhand der Dateinamen im Verzeichnis eine Liste aller (musiktechnisch)
    # vorhandene Playlisten erzeugen
    pl_file_ending = ".m3u"              # Dateiendung der Playlisten
        
    playlistlist = os.listdir(path)
    # Dateiendung der Playlisten entfernen
    return [ i.replace(pl_file_ending, "") for i in playlistlist if i.endswith(pl_file_ending)]
    
    
def update_all_playlists(Music_path, Playlist_path):
    # Die Dateistruktur in Music_Path in eine MPD-taugliche Liste
    # von Playlisten-Dateien im Ordner Playlist_path anlegen. 
    # Die bisherigen dateien werden vorher komplett geloescht, es wird alles neu geschrieben.
    # Damit werden Veränderungne von einzelnen Titeln innerhalb eines Musikordners auch erkannt. 
    # Dauer bei ca. 100 Playlisten: 0.6 Sekunden
    # Am Schluss dann mpd updaten!

    start = time.time()
    music_file_endings = ('.mp3','.m4a', '.wav', '.wma','.aac' )     # zulaesige Dateiendungen fuer Musiktitel
    pl_file_ending = '.m3u'

    # Vorhandene Musik und Playlisten laden

    # nur alle Ordner im Musikverzeichnis!!!
    # nur lokale Ordnernamen, der Rest ist im MPD als Default-Musikordner festgelegt!

    music_path = Path(Music_path)
    playlist_path = Path(Playlist_path)

    musiclist = [e for e in music_path.iterdir() if e.is_dir()]

    # Internetradio: alle Datein auf Ebene der Ordner (mit Endung einer Playliste!)
    # mit Hinweis auf Internetradio versehen!
    radiolist = [e for e in music_path.iterdir() if e.is_file() and e.suffix in pl_file_ending]
    print('radiolist:')
    print(radiolist)

    # Aufraumen aller alten Playlisten 
    for j in list(playlist_path.glob('*.m3u')):
        j.unlink() 

    # Erst Internetradio: Dateien kopieren und umbenennen 
    # ( Zieldateipfad wird erstellt, dann gefuellt )
    for i in radiolist:
        target = playlist_path / (i.stem + '_InternetRadio' + i.suffix)
        target.write_text(i.read_text())


    # Alle Musikdateien des Ordners auslesen, 
    # sortieren, 
    # Dateinamen in die palylistendatei schreiben
    for i in musiclist:

        # nur Musikdateien verwenden.
        songs = [str(ii) for ii in list(i.glob('*.*')) if ii.suffix in music_file_endings ]   
        songs.sort()

        # Playlistendatei anlegen und mit Liste der songs fuellen
        target = playlist_path / (i.stem+pl_file_ending)
        pl_text = ''
        for xx in songs:
            pl_text += f'{xx}\n'
        target.write_text(pl_text)
    

    print(f'playlisten erzeugt')  
    print(f'benötigte Zeit: {start-time.time()}')   


            
    subprocess.Popen(["sudo", "mpc", "update"], stdout=subprocess.PIPE)



def load_file(filename, filename_dflt):
    # Informationen mittel HJSON aus einer Datei einlesen und zurueckgeben
    try:
        with open(filename,'r') as fobj:
            return hjson.load(fobj)      
    except FileNotFoundError:
        print(f'file not found: {filename}, opening {filename_dflt} instead.')
        with open(filename_dflt,'r') as fobj:
            return hjson.load(fobj)  
    except:
        print(f'problem loading: {filename}')

    return None  

def split_lines(text, linelen):
    # - Trenner gefunden, 
    # - alle unnoetigen Trennstriche entfernen
    # - letzten Trennstrich stehen lassen
    # - Leerzeichen entfernen
    # Ergebnis: laenge des resultierenden Strings 

    lines=[]
    temp = text
    cut = 0

    while len(temp)>linelen:
        temp=temp.strip(' ')
        temp=temp.strip('-')

        # Trennstelle finden
        # Leerzeichen eins mehr, weil man das Leerzeichen am Ende nicht braucht. Den Trennstrich schon. 
        cut = max(temp.rfind(' ',0, linelen+1),temp.rfind('-',0, linelen)) 
        # kein Trenner gefunden -> komplette Zeile ohne Trenner nehmen  
        if cut==-1: 
            cut=linelen
        # potentielle Trenner innerhalb der Zeile entfernen,
        # nicht aber den bereits gefundenen Trenner
        temp=temp[0:cut-1].replace('-','')+temp[cut-1:]

        # 1. Iteration
        cut = max(temp.rfind(' ',0, linelen+1),temp.rfind('-',0, linelen)) 
        # kein Trenner gefunden -> komplette Zeile ohne Trenner nehmen  
        if cut==-1: 
            cut=linelen
        temp=temp[0:cut-1].replace('-','')+temp[cut-1:] 

        # 2. Iteration
        cut = max(temp.rfind(' ',0, linelen+1),temp.rfind('-',0, linelen)) 
        # kein Trenner gefunden -> komplette Zeile ohne Trenner nehmen  
        if cut==-1: 
            cut=linelen           

        # jetzt je nach Trennertyp
        if temp[cut] == ' ':
            lines.append(temp[0:cut])
            print(temp[0:cut])
            # Fuehrendes Leerzeichen bei dem Reststring entfernen
            temp = temp[cut+1:]
        elif temp[cut] == '-':
            lines.append(temp[0:cut+1])
            print(temp[0:cut+1])
            # Fuehrendes Leerzeichen bei dem Reststring entfernen
            temp = temp[cut+1:]


    # letzte halbvolle Zeile hinuzfuegen, ohne Silbentrenner    
    lines.append(temp.replace('-',''))
    return lines
    

def add_numbering(text_list):
    # Zeilennummern hinzufuegen, dabei aber eine neue Stringliste erzeugen!
    # Zeilennummer beginnen bei 1
    new_list = []
    for i,txt in enumerate(text_list):
        new_list.append(f'{(i+1) % 10}'+txt)
    return new_list

def days_since(str_date):
    # gibt die Tage seit einem Datum aus. 
    # Ergebnis ist bei Tagen in der Vergangenheit negativ!
    delta =  date.fromisoformat(str_date) - date.today()
    return delta.days



# function to get ip address of given interface
def get_ip_address():
    try:
        ip_address = ''
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8",80))
        ip_address = s.getsockname()[0]
        s.close()
    except:
        ip_address = "no conecction, no IP"

    return ip_address

# Konstanten: Positonsnummern im self.PIN array
PIN_LED  = 0
PIN_NEXT = 1
PIN_PREV = 2


def block_wifi():
    # WLAN blockieren mit Software
    subprocess.Popen(['sudo', 'rfkill', 'block', 'wifi'], stdout=subprocess.PIPE)

def unblock_wifi():
    # WLAN blockieren mit Software: entsperren
    # todo: leider mit kryptischem Geraeteneman und ohne IP, daher derzeit nicht verwendet
    subprocess.Popen(['sudo', 'rfkill', 'unblock', 'wifi'], stdout=subprocess.PIPE)

def dict_from_folder(foname):
    # dictionary anhand der audiodateien in einem Ordner foname erstellen, fuer die Ansagetexte
    # anhand des Dateinemens xxxx_1.mp3 wird im dictionary der key 'xxxx' erzeugt. 
    # (getrennt wird immer der Namensteil vor dem ersten Underscore.) Der Eintrag dazu ist 
    # eine Liste mit allen Dateien, die 'xxxx' im Dateinamen enthalten.
    sound_msg = {}

    p=Path(foname)

    # todo: Ansagetexttypen automatisch aus den vorhandenen Dateinamen erzeugen, (regular expressions)
    for i in p.iterdir():
        # nur Namensteil vor dem Nummerntrenner, also von "hallo_1.mp3" nur "hallo"
        naked = i.name.split('_')[0]
        # fuer neue Namensteile einen Eintrag erzeugen
        if not naked in sound_msg.keys():
            sound_msg[naked] = []

    # alle passenden Dateien zur Suchmaske ausgeben
    for i in sound_msg.keys():
        sound_msg[i] = list(p.glob(f'{i}*.mp3'))

    return sound_msg     


class StateMachine():
# - die Button-callbacks als Methoden
# - verwaltet den MPD-Client
# - steuert die Musikwiedergane an MPD
# - steuert die Lautstaerke ueber ALSA
# - lädt und speichert die aktuele Playlistposition
# - aktualisiert das Display     

    # lage Liste aller Konstanten
    # Backlight control
    BL_OFF = "OFF"
    BL_ON  = "ON"
    BL_OnBUTTON = "OnButton"

    # ID der Buttons
    # (hat nix mit den tatsaechlichen GPIOs zu tun)
    BU_NONE = 0
    BU_PREV = 1
    BU_NEXT = 2
    BU_PAUSE = 3
    BU_PAUSE_ROTATION = 4
    BU_VOLUME_ROTATION = 5

    # Haupt-Zustaende
    ST_INIT = 100
    ST_PLAY = 200
    ST_PAUSE = 300
    ST_WAIT = 400
    ST_LOADLIST = 500
    ST_SHUTDOWN = 600
    ST_EDIT_START = 700
    ST_EDIT_PAIR = 800
    ST_EDIT_CHECK = 900
    ST_EDIT_CORR = 1000
    ST_EDIT_SET = 1100
    ST_BLOCKED = 1200
    ST_INTERNET_RADIO = 1300
    ST_ERROR_DISPLAY = 1400
    ST_CHOOSE_PLAYLIST = 1500

    NO_DISP = 0
    DISP_PLAY = 1
    DISP_UNKNOWN_ID = 2
    DISP_WAIT = 3
    DISP_MESSAGE = 4

    NO_NEWSTATE = -1
    NO_RFID     = False
    NO_PLAYLIST = "no_playlist"


    def __init__(self, RFID_reader, LCD, PINS,
                 setupfile='/home/dietpi/settings_and_data/base_settings.ini'):
        # Pinreihenfolge von PINS:
        # PIN_LED  = 0
        # PIN_NEXT = 1
        # PIN_PREV = 2
        self.logger = logging.getLogger(__name__)  

        # zentrales Objekt das verwaltet wird: der MPD-CLient!!!
        self.cl = mpd.MPDClient()
        try:
            self.cl.connect('localhost',6600)
        except:
            self.logger.info('__init__: MPD-Client nicht da')

        # RFID-reader
        self.reader = RFID_READER_PN532()
  
        # LCD-Display
        self.LCD = LCD
        self.LCD.noCursor()

        if len(PINS) != 3:
            self.logger.error('Falsche Anzahl Pins!')
        self.PINS = PINS
        
        # GPIOs zuweisen
        self._init_GPIO()

        # setup-file
        self.setupfile = setupfile

        # einmaliger start ins Editiermenue? Wenn beide Tasten gedrueckt sind!
        # Muss nach dem initialisieren der Pins kommen!
        self.editstart = ( GPIO.input(self.PINS[PIN_NEXT])==False and GPIO.input(self.PINS[PIN_NEXT])==False )

        # interne Variablen fuer den Ablauf
        self.state = self.ST_INIT
        self.newstate = self.ST_INIT
        self.laststate = self.NO_NEWSTATE

        self.F_button = self.BU_NONE      # Flag, ob ein Tastwndruck erkant wurde
        self.N_button = 0            # Anzahl der Tasteninteraktionen
        self.F_shutdown = False         # Zustandsflag Shutdown durch Bediner angeforder
        self.F_shutdownCalled = False   # Zustandsflag Shutdown initialisiert

        self.F_RFID = self.NO_RFID        # Zustandsflag RFID, False oder integer
        self.F_update_display = False# Displayupdate erzwingen

        self.cur_disp_page = self.NO_DISP   

        # Variablen fuer das Editiermenue
        self.playlists = {}          # Liste aller Playlisten: {Playlist : UID}
        self.playlist_internetradio = False  # Playliste ist Internetrasio?
        self.def_playlists = {}              # alle Playlisten mit RFID, {playlist1:UID1, playlist2:UID2, ...}
        self.undef_playlists = {}            # alle undefinierten Playlisten
        self.all_pl = {}                     # Fuer den Zustand xxx, Liste aller abspielbaren Playlisten
        self.temp_uid_dict = {}  
        self.mode_keys = []         # Liste der aktuell angezeigten Auswahlelemente
        self._index_key = 0         # Nummer des gerade im Editiermenue angezeigten Elementes
        self.setup = {}      

        self.disp_list = []         # Zeilen der Menieliste
        self.list_index = 0         # Aktuelle Auswahl der Zeilen
        self.help_list = []         # Text Hilfemenue in Zeilen
        self.help_index = 0         # aktuelle Zeilennummer von Help_list in der obersten Displayanzeige

        self.exception = None       # Platz fuer das Fehlerhandling

        # Variablem mit Informationen der Musikwiedergabe
        # Infoliste, die vom Display abgefragt wird und in Datei abgespeichert wird. Es werden immer alle Eintraege erwartet.
        self.info =     {'volume'       : 0,
                         'volume_disp'  : 0,       # Volumen fuer das Display, max immer bei 100%
                         'state'        : '',          # stop, pause, play
                         'song_number'  : '0',
                         'elapsed_time' : 0.0,
                         'title'        : '-',
                         'len_playlist' : '-1',            # Anzahl der Titel in der Playlist fuer zyklisches Verhalten bei NEXT
                         'playlist'     : self.NO_PLAYLIST,
                         'duration'     : 0.0,          # Dauer des aktuellen titels
                         'name'         : 'unbekannt', # Name des Internetradios
                         }        

        # allgemeine Paramtrierung laden
        with open(setupfile,'r') as fobj:
            temp_dict = hjson.load(fobj)
            self.cfg_gl = temp_dict['global']             # globale Einstellungen fuer alle Klassen
            cfg = temp_dict['StateMachine']          # spezifische Einstellungen nur fuer diese Klasse
            self.linewidth = temp_dict['DisplayHandler']['line_width'] # Zeilenbreit Display

        # Werte, die aus dem setupfile uebernommen werden,
        # einmaliges Laden, andere Werte nur duch Editieren im setupfile moeglich.
        self.cycletime          = cfg['cycletime']                 # in Sekunden, Zyklus Reaktion Tasten
        self.ct_display_play    = cfg['ct_display_play']           # in Sekunden, Zyklus Displayupdate
        self.ct_display_edit    = cfg['ct_display_edit']           # in Sekunden, Zyklus Displayupdate
        self.cycletime_RFID     = cfg['cycletime_RFID']            # in Sekunden, Zyklus zum Auslesen der RFID
        self.waitButtonShutdown = cfg['waitButtonShutdown']        # in Sekunden, erforderliche Dauer Tastendruck
        self.message_display    = cfg['message_display']           # in Sekunden, Anzeigezeit von Messages
        self.sleep_uid_update   = cfg['sleep_uid_update']          # in Sekunden, leeres Display, wenn eine neue RFID ausgelesen wurde
        self.sleep_uid_display  = cfg['sleep_uid_display']         # in Sekunden, Pausierung, um neue UID im Editiermenue im Display anzuzeigen
        self.duration_LED_action= cfg['duration_LED_action']       # in Sekunden, minimale Leuchtdauer LED_ACTION, bei Button oder RFID
        self.user = load_file(self.cfg_gl['fname_user'], self.cfg_gl['fname_dflt_user'])    # Liste aller Benutzer, fuer Begruessung
        self.msg_vol = cfg['msg_vol']                              # Lautstaerke der Sprachinformatinen
        
        # Liste der Mastercard-UIDs laden, Strings
        self.MasterCardID = load_file(self.cfg_gl['fname_mc'], self.cfg_gl['fname_dflt_mc'])



        #try:
        # Ansagetexte laden
        # todo: sprachspezifische Ansagetexte --> 3 verschiedenen Dictionaries, fuer jede Sprache eines 
        # in der struktur: 'hello_de_01.mp3'
        
        # Liste mit dictionaries fuer: 
        # Ansagetext 'hello', Sprachindividuelle Texte fuer den Rest
        self.sound_msg_dicts = {}

        # custumized Ansagetexte fuer hello verwenden, sofern darin passende Dateien vorhanden sind. 
        # Falls nix hinterlegt ist, entsteht ein leeres dictionary. Im Code wird dann auf das sprachspezifische 
        # dict zugegriffen, in dem die default Ansagen fuer 'hello' liegen.
        self.sound_msg_dicts['hello'] = dict_from_folder(self.cfg_gl['foname_audio_msg_hello_c'])

        # jetzt die sprachspezifischen laden, 
        # leider haesslich and die Namen der geladenen Sprache gekoppelt.
        self.sound_msg_dicts['D '] = dict_from_folder(self.cfg_gl['foname_audio_D'])
        self.sound_msg_dicts['GB'] = dict_from_folder(self.cfg_gl['foname_audio_GB'])
        self.sound_msg_dicts['Cz'] = dict_from_folder(self.cfg_gl['foname_audio_Cz'])

        # Nachrichten fuer das Display laden, in allen Sprachen
        with open(self.cfg_gl['fname_messages']) as fobj:
            self.msg_dict = hjson.load(fobj)


        # Werte die via Editiermenue zugaenglich sind und eingestellt werden, Platzhalter
        # Die eigentlichen Zahlenwerte werden im INIT geladen.
        self.shuffle_step       = 10.0            # in Sekunden
        self.vol_max            = 100             # in %
        self.vol_step           = 3               # in %
        self.BacklightMode      = self.BL_ON
        self.Timeout_backLight  = 2               # in Sekunden, nur bei BL_OnBUTTON
        self.timeout_shutdown   = 1200            # in Sekunden
        self.lg                 = 'D '            # Sprachwahl


        # timer-Variablen erstellen
        self.timer_start=[]
        self.timer_length=[]

        # Verzeichnis der Zustandsfunktinen erstellen
        self.state_dict = {
                        100 : self.DO_ST_100,
                        150 : self.DO_ST_150,
                        160 : self.DO_ST_160,
                        170 : self.DO_ST_170,
                        200 : self.DO_ST_200,
                        250 : self.DO_ST_250,
                        300 : self.DO_ST_300,
                        350 : self.DO_ST_350,
                        400 : self.DO_ST_400,
                        450 : self.DO_ST_450,
                        500 : self.DO_ST_500,
                        600 : self.DO_ST_600,
                        650 : self.DO_ST_650,
                        700 : self.DO_ST_700,
                        705 : self.DO_ST_705,
                        710 : self.DO_ST_710,
                        790 : self.DO_ST_790,
                        795 : self.DO_ST_795,
                        800 : self.DO_ST_800,
                        805 : self.DO_ST_805,
                        810 : self.DO_ST_810,
                        820 : self.DO_ST_820,
                        825 : self.DO_ST_825,
                        830 : self.DO_ST_830,
                        835 : self.DO_ST_835,
                        840 : self.DO_ST_840,
                        845 : self.DO_ST_845,
                        890 : self.DO_ST_890,
                        895 : self.DO_ST_895,
                        900 : self.DO_ST_900,
                        910 : self.DO_ST_910,
                        950 : self.DO_ST_950,
                        955 : self.DO_ST_955,
                        958 : self.DO_ST_958,
                        959 : self.DO_ST_959,
                        990 : self.DO_ST_990,
                        995 : self.DO_ST_995,
                        1000 : self.DO_ST_1000,
                        1005 : self.DO_ST_1005,
                        1010 : self.DO_ST_1010,
                        1020 : self.DO_ST_1020,
                        1025 : self.DO_ST_1025,
                        1030 : self.DO_ST_1030,
                        1031 : self.DO_ST_1031,
                        1032 : self.DO_ST_1032,
                        1033 : self.DO_ST_1033,
                        1035 : self.DO_ST_1035,
                        1039 : self.DO_ST_1039,
                        1050 : self.DO_ST_1050,
                        1051 : self.DO_ST_1051,
                        1055 : self.DO_ST_1055,
                        1056 : self.DO_ST_1056,
                        1059 : self.DO_ST_1059,
                        1060 : self.DO_ST_1060,
                        1065 : self.DO_ST_1065,
                        1069 : self.DO_ST_1069,
                        1070 : self.DO_ST_1070,
                        1075 : self.DO_ST_1075,
                        1080 : self.DO_ST_1080,
                        1085 : self.DO_ST_1085,
                        1090 : self.DO_ST_1090,
                        1095 : self.DO_ST_1095,
                        1100 : self.DO_ST_1100,
                        1105 : self.DO_ST_1105,
                        1110 : self.DO_ST_1110,
                        1120 : self.DO_ST_1120,
                        1125 : self.DO_ST_1125,
                        1130 : self.DO_ST_1130,
                        1190 : self.DO_ST_1190,
                        1195 : self.DO_ST_1195,
                        1200 : self.DO_ST_1200,
                        1250 : self.DO_ST_1250,
                        1300 : self.DO_ST_1300,
                        1350 : self.DO_ST_1350,
                        1400 : self.DO_ST_1400,
                        1450 : self.DO_ST_1450,
                        1500 : self.DO_ST_1500,
                        1505 : self.DO_ST_1505,
                        1550 : self.DO_ST_1550,
                        1555 : self.DO_ST_1555,
                        1590 : self.DO_ST_1590,
                        1595 : self.DO_ST_1595,
                        1599 : self.DO_ST_1599
        }

        # Eingabemaske erstellen
        # Displaylaenge, max. Zeichen vor dem Curser, Blinkrate
        self.input = TextInput(self.linewidth, cfg['input_display_currentpos'],cfg['input_frequency'])
        # speicher fuer die wlaninfo [name, paswort] (nur temporaer)
        self.wlaninfo= ['','']

        # Eigentlich eine Info, aber auf das Hoehre Level gezogen, um tatsaechlich das logging zu sehen
        self.logger.warning('Init StateMachine fertig.')  

        self.LCD.clear()
        self.LCD.write_lines(self.msg_dict["100"][self.lg],0,1)


        self.DO_ST_100()


    #+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    #+++++++++++++++++++++++++++++++++  Ende self._init_ +++++++++++++++++++++++


    def _on_button(self, button_id, direction=+1):
        # allgemeine Vorlage zum Verarbeiten von Tasteingaben
        if self.F_button != button_id:
            self.F_button = button_id
            self.N_button = direction
            self.logger.info(f'button_id: {button_id}')
        else:
            # Taste bereits vorgemerkt, Anzahl anpassen
            self.N_button += direction
            self.logger.info(f'N_button: {self.N_button}')
        
        # LED_ACTION einschalten! 
        GPIO.output(self.PINS[PIN_LED], GPIO.HIGH)
        self.start_timer(self.TIMER_LED)

        if self.BacklightMode == self.BL_OnBUTTON:
            self.LCD.setBacklight(GPIO.HIGH,0)
            self.start_timer(self.TIMER_BACKLIGHT)

    # Alle Callbacks fuer das Tastenhandling
    def OnPrevButton(self, pin):
        # callbackfunktion fuer den Taster Prev
        self._on_button(self.BU_PREV)

    def OnNextButton(self, pin):
        # callbackfunktion fuer den Taster Next
        self._on_button(self.BU_NEXT)

    def OnPauseButton(self, pin):
        # callbackfunktion fuer den Taster Pause
        self._on_button(self.BU_PAUSE)

    def OnPauseRotary(self, pin, direction):
        # calback fuer rotary change Pause
        self._on_button(self.BU_PAUSE_ROTATION, direction)

    def OnVolumeRotary(self, pin, direction):
        # calback fuer rotary change Volume
        self._on_button(self.BU_VOLUME_ROTATION, direction)

    def OnShutdownButton(self, pin):
        # callback fuer Volume-switch -> shutdown
        # Reaktion wird ausserhalb von self.newstate oder self.F_button abgehandelt. 
        # damit ist ein versehentliches Ueberschreiben durch den restlichen Ablauf ausgeschlossen
        self.logger.info('Shutdown-button gedrueckt')

        self.timer_shutdown = time.time()

        while (self.F_shutdown == False) and (GPIO.input(pin) == GPIO.LOW):
            time.sleep(0.100)
            # Nach ablauf der Mindestzeit immer noch gedrueckt -> Shutdown initieren und 
            # Schleife verlassen
            if (time.time() - self.timer_shutdown) >  self.waitButtonShutdown:
                self.F_shutdown = True
                self.logger.info('Shutdown initiiert.')

    # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # ++++++++++++++++++++++++ Hilfsfunktionen +++++++++++++++++++++++++++++++++++
    # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    def init_timer(self, length):
        # Einen Timer definieren, eine Timer_ID wird zurueckgegeben
        # der Timer wird in dem Moment auch gleich gestartet.
        self.timer_length.append(length)
        self.timer_start.append(time.time())
        return len(self.timer_length)-1

    def get_time(self, TIMER_ID):
        # verstrichene Zeit abfragen
        return time.time() - self.timer_start[TIMER_ID]

    def elapsed_time(self,TIMER_ID):
        # Vergleicht die verstrichene Zeit seit dem letzen Timerstart mit 
        # der definierten Timerlaenge
        # Rueckgabe von True, wenn der Timer abgelaufen ist, 
        return self.get_time(TIMER_ID) > self.timer_length[TIMER_ID]

    def remaining_time(self,TIMER_ID):
        # Zeit, bis der Timer abgelaufen ist
        return self.timer_length[TIMER_ID] - self.get_time(TIMER_ID)

    def start_timer(self, TIMER_ID):
        # Timer jetzt neu starten
        self.timer_start[TIMER_ID] = time.time()

    def checkShutdown(self):
        # Abfragen, ob bald Ausgeschaltet wird, im WAIT und PAUSE

        if int(self.remaining_time(self.TIMER_AUTOSHUTDOWN)) == 60:
            self.play_sound_msg('autoshutdown')

        if self.elapsed_time(self.TIMER_AUTOSHUTDOWN):
            self.newstate = self.ST_SHUTDOWN
            self.logger.info('checkShutdown: Timeout Autoshutdown')


    def generate_footer(self, prev="BACK", updown=True, pause="OK", next="HELP", leftright=False):
        # Fusszeile mit Tastenbelegung fuer die Menues erstellen, 
        # mit variablen Elementen

        if prev:
            prev_str=prev
        else:
            prev_str='    '

        if updown==True:
            # Pfeile hoch/runter im DisplayHandler auf den freien Zeichen
            up_str = chr(6)
            down_str = chr(7)
        elif leftright==True:
            # Belegung der Pfeile im DOGLCD fest vorgegeben
            up_str = chr(0x7F)
            down_str = chr(0x7E)
        else:
            up_str = ' '
            down_str = ' '

        if pause:
            try:
                pause_str = pause[0:2]
            except IndexError:
                # wahrscheinlich nur ein Zeichen
                pause_str = pause
        else:
            pause_str = '  '

        if next:
            next_str = next
        else:
            next_str = '    '
        
        return f'{prev_str.ljust(4)} {up_str} {pause_str} {down_str} {next_str.rjust(4)}'

    def add_footer_help(self):
        # Fusszeile fuer die Hilfe hinzufuegen, 
        # + sicherstellen, dass der Hilfetext 2 Zeilen lang ist.   
        while len(self.help_list) < 2:
            self.help_list.append(" ")

        self.help_list.append(self.generate_footer(pause=False, next=False))

    def update_MPD_info(self):
        # aktuelle Werte von self.info fuellen
       
        # Erstmal die Infos, die nicht von MPD kommen oder geradenicht aktualisiert werden
        # self.info['volume']          wird direkt geschrieben
        # self.info['playlist']          wird direkt geschrieben
        # self.info['len_playlist']    beim Laden der Playliste aktualisiert
        
                    
        # Jetzt die Infos von MPD, sofern eine Verbindung besteht.  
        if self._CheckConnection():
            currentsong = self.cl.currentsong()
            status = self.cl.status()
        else:
            currentsong = {}
            status = {}

        
        # jetzt beschissene Rueckgsben vom MPD-Client abfangen
        try:
            # Wertebereich: 'play', 'pause', 'stop'
            self.info['state'] =  status['state']
        except KeyError:
            self.info['state'] =  '-'
        
        try:
            self.info['song_number'] = currentsong['pos']   
        except KeyError:
            self.info['song_number'] = '--'
            
        try:
            self.info['elapsed_time'] = status['elapsed']
        except KeyError:
            self.info['elapsed_time'] = '0.0'

        try:
            self.info['title'] = currentsong['title']
        except KeyError:
            self.info['title'] = '-'

        try:
            self.info['name'] = currentsong['name']
        except KeyError:
            self.info['name'] = 'unbekanntes Radio'

        try: 
            self.info['len_playlist'] = status['playlistlength']
        except KeyError:
            self.info['len_playlist'] = '-1'  

        # dauer des aktuellen Titels, nur relevant fuer das Spulen!
        try: 
            self.info['duration'] = float(status['duration'])
        except:
            self.info['duration'] = 0.0  

        self.logger.debug("self.info: "+str(self.info))

    def adjust_volume(self, delta_volume):
        # Lautstaerke um den Wert delta_volume veraendern
        new_volume = self.info['volume'] + delta_volume

        # Min und Maxwert einhalten
        new_volume = max(0, new_volume)
        new_volume = min(self.vol_max, new_volume)

        subprocess.Popen(["sudo", "amixer", "set", "Master", '{:02d}%'.format(new_volume)], stdout=subprocess.PIPE)

        self.info['volume'] = new_volume

        self._rescale_volume_disp()

    def play_sound_msg(self,list_name):
        # Aus der uebergebenen Liste an Sound-eldungen ein zufaelliges Element abspielen
        # In einer Liste sind typischerweise nur Elemente zu einem Thema
        # Wiergabelautstaerke anpassen

        try:
            if (list_name == 'hello') and (self.sound_msg_dicts['hello'] !={}):
                # fuer hello inner das dictionary hello laden, das nur den key hello hat, sofern nicht leer.  
                auswahl = self.sound_msg_dicts[list_name][list_name]
            else:
                # sonst das sprachspezifische dict laden, und dort die entsprechende liste raussuchen
                auswahl = self.sound_msg_dicts[self.lg][list_name]
        except:
            # Gab es einen Fehler beim laden --> leere Liste, um nur die Ersatzmeldung abzuspielen
            self.logger.error('keine Datei dazu gefunden')
            auswahl = self.sound_msg_dicts[self.lg]['noaudio']

        # eine zufaellige davon abspielen
        subprocess.Popen(["sudo", "amixer", "set", "Master", '{:02d}%'.format(self.msg_vol)], stdout=subprocess.PIPE)

        # Soundmessages mit call ausgeben, weil es solagne wartet, bis es fertig ist. Sonst kriegt MPD Probleme...
        # den vollen Pfad ausgeben mit .resolve()
        if len(auswahl) > 0:
            subprocess.call(f'sudo mpg123 {auswahl[randint(0,len(auswahl)-1)].resolve()}', shell=True)
            self.logger.debug(f'play_sound_msg: {auswahl[randint(0,len(auswahl)-1)].resolve()}')
        else:
            self.logger.error(f'play_sound_msg: Keine Wiedergabedatei fuer Aktion: {list_name}')

        # Lautstaerke der Musikwiedergabe sofort wiederherstellen
        self.adjust_volume(0)

    def save_current_position(self):
        # aktuelle Infos vom MPD in eine Datei abspeichern
        with open(self.cfg_gl['fname_last_pos'], 'w') as fobj:
            hjson.dump(self.info, fobj)
        self.logger.info(f"{self.state}: save_current_position: "+str(self.info))


    def load_position(self):
        # letze Musikwiedergabeposition laden, Wiedergabe von true, wenn eine aktive Position gefunden wurde

        try: 

            self.logger.debug(self.cfg_gl['fname_last_pos'])
            with open(self.cfg_gl['fname_last_pos'], 'r') as fobj:
                self.info = hjson.load(fobj)
            self.logger.info("nach laden last_pos: "+str(self.info))
            return True
        except:
            # Nicht erfolgreich geladen
            self.logger.error('load_position nicht erfolgreich.')
            return False

    def save_to_file(self):
        # alle Einstellungen und Playlistenspeichern

        # Settings in Datei speichern
        with open(self.cfg_gl['fname_setup'], 'w') as fobj:
            hjson.dump(self.setup,fobj)

        # Playlisten in der Zuordnung {Playlist:UID} abspeichern
        with open(self.cfg_gl['fname_pl'], 'w') as fobj:
            hjson.dump(self.playlists,fobj)        

        # umgedrehte Zuordnung {uid:playlist} erstellen und speichern
        temp = {}
        for key, val in self.playlists.items():
            temp[val]=key
        with open(self.cfg_gl['fname_uid_list'], 'w') as fobj:
            hjson.dump(temp,fobj)  

        # Mastercard-Liste speichern
        with open(self.cfg_gl['fname_mc'],'w') as fobj:  
            hjson.dump(self.MasterCardID, fobj)                      

    def load_uptime(self):
        # abgespielte Zeit und Datum speichern
        try: 
            with open(self.cfg_gl['fname_uptime'], 'r') as fobj:
                self.time_manager.load(fobj)
        except FileNotFoundError:
            self.logger.error('load_uptime nicht erfolgreich, default geladen')
            with open(self.cfg_gl['fname_dflt_uptime'], 'r') as fobj:
                self.time_manager.load(fobj)

        self.logger.info("nach laden uptime: "+str(self.time_manager.get_uptime()))
        return True

    def save_uptime(self):
        # abgespielte Zeitdauer und Datum speichern
        with open(self.cfg_gl['fname_uptime'], 'w') as fobj:
            self.time_manager.save(fobj)
    def _check_prev(self):
        # gibt es einen Titel vor dem aktuellen? Rueckgabe bool!
        # einfach: sind wir in Titel > 1 
        # True: es gibt einen vorherigen Titel der Playliste
        # False: kein weiterer Titel
        if self.info['song_number'].isnumeric():
            return int(self.info['song_number']) > 0
        else:
            return False
    def _check_next(self):
        # gibt es einen Titel nach dem aktuellen? Rueckgabe bool!
        # title < len_playlist
        # True: es gibt eine weiteren Titel der Playliste
        # False: kein weiterer Titel
        if self.info['song_number'].isnumeric() and self.info['len_playlist'].isnumeric():
            # song_number beginnt bei 0, len_playlist immer bei 1
            return int(self.info['song_number']) < ( int(self.info['len_playlist']) - 1 )
        else:
            return False


    def _rescale_volume_disp(self):
        # Volume fuer das Display skalieren, so dass Maximum immer mit 100% angezeigt wird
        print(self.info['volume'])
        print(self.vol_max)

        self.info["volume_disp"] = int(self.info['volume'] * (100.0/ self.vol_max)) 

    def _index_up(self):
        # self._index_key zyklisch durchlaufen
        self._index_key = (self._index_key + 1) % len(self.mode_keys)

    def _index_down(self):
        # self._index_key zyklisch durchlaufen
        self._index_key = (self._index_key - 1) % len(self.mode_keys)

    def _ch_val(self, direction):
        # Wert des aktuell angezeigtzen Setup-items veraendern, 

        # auf Laenge der Liste limitieren!
        max_index = len(self.setup[self.mode_keys[self._index_key]][1])
        cur_index = self.setup[self.mode_keys[self._index_key]][0]

        # index anpassen, aber begrenzen auf die Liste

        cur_index = (cur_index+direction) % max_index

        
        # angepassten Index uebernehmen
        self.setup[self.mode_keys[self._index_key]][0] = cur_index

    def _ch_index(self,direction):
       # Zeilennummer bei einer Listenanzeige im Editiermenue anpassen
       self.list_index += direction
       self.list_index = max(1,self.list_index)
       self.list_index = min(len(self.disp_list)-2,self.list_index)

    def _ch_help_index(self,direction):
       # Zeilennummer bei einer Listenanzeige im Editiermenue anpassen
       self.help_index += direction
       self.help_index = max(0,self.help_index)
       self.help_index = min(len(self.help_list)-3,self.help_index)


    def _getval(self,key, offset=0):
        # aktuellen Wert eines bestimmten Setup-items abfragen 
        # oder den Nachbarwert abfragen mit Offset
        index = self.setup[key][0]
        val_range = self.setup[key][1]

        return val_range[(index+offset) % len(val_range)]

    def _check_internet(self):
        # rueckgabe, ob WLAN-Verbindung zu irgendwas besteht
        status, result = subprocess.getstatusoutput("ping -c1 -w2 8.8.8.8")

        if status == 0:
            return True
        else:
            return False


    def get_val_string(self):
        # String fuer das Editiermenue mit den Einstellungen erzeugen
        dv = []
        for i in [-1,0,1]:
            item = self._getval(self.mode_keys[self._index_key],i)
            # in einen String umwandeln?
            if isinstance(item, int):
                dv.append(str(item))
            elif isinstance(item,str):
                if len(item) > 4:
                    dv.append(item[0:4])
                else:
                    dv.append(item)
        
        # wenn das anzuzeigende Element zu lang ist: nur das aktuelle Element anzeigen
        if len(str(dv[1])) > 4:
            result = str(dv[1])
            result = '[' + result + ']'
            return result.center(self.linewidth)     

        else:
            # String erstellen und zurueckgeben            
            return f'{dv[0]:<4s} [{dv[1]:^4s}] {dv[2]:>4s}'      


    def _isUID(self, item):
        # Testen, ob es sich um eine korrekte UID handelt
        # eigentlich Laenge 12, kann baer auch nur 11-stellig sein.
        if isinstance(item,str) and len(item)>10 and len(item)<=12:
            if item.isnumeric():
                return True

        return False
    def _CheckConnection(self, iterations=2):
        # Verbindung zum MPDClient sicherstellen
        try:
            self.cl.ping()
            return True
        except mpd.ConnectionError:
            self.logger.info('no connection mpd, but try to')
            try:
                self.cl.connect("localhost", 6600) 
                time.sleep(0.05)
                    
            except ConnectionRefusedError:
                return False

            # wenn keine Verbindung besteht --> nochmal versuchen, 
            if iterations>0:
                return self._CheckConnection(iterations-1)
            else:
                return False

    # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # ++++++++++++++++++++++++ Displayfunktionen   +++++++++++++++++++++++++++++++
    # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

    def _writeMessage(self, message, start=0, length=3, clear=True):
        # Im Display eine einmalige Info darstellen, die anschliessend wieder ueberschrieben wird
        self.cur_disp_page = self.DISP_MESSAGE
        if clear:
            # Display leeren und alle Laufschriften deaktivieren
            self.LCD.clear()
            self.LCD.ls_active = 0

        self.LCD.write_lines(message, start, length)
        self.start_timer(self.TIMER_MESSAGE)
        self.logger.info(message)


    def _writePlay(self):
        # Playliste und Titel fuer die normale Musikwiedergabe in die Laufschrift des Displays laden
        if self.cur_disp_page != self.DISP_PLAY:
            self.LCD.clear_data()
            self.cur_disp_page = self.DISP_PLAY
        
        self.LCD.write_info(self.info)
        self.logger.debug("250: self.LCD.write_info(self.info)")
        self.logger.debug(self.info)

    def _writeRadio(self):
        # Playliste und Titel fuer die Wiedergabe Internetradio
        if self.cur_disp_page != self.DISP_PLAY:
            self.LCD.clear()
            self.LCD.clear_data()
            self.cur_disp_page = self.DISP_PLAY
        
        self.LCD.write_radio_info(self.info)


    def _validMessage(self):
        # prueft, ob gerade noch eine message angezeigt werden soll
        # True: es wird eine Message angezeigt werden, und die Zeit ist nicht abgelaufen
        # False: es wird keine Message angezeigt, oder die Zeit dafuer ist abgelaufen 
        if self.cur_disp_page == self.DISP_MESSAGE:
            if self.elapsed_time(self.TIMER_MESSAGE):
                return False
            else:
                return True
        else:
            return False

    def _write_disp_list(self):
        # aktuell relevante Zeilen fuer das Editiermenue schreiben,
        # jede Zeile einzeln, 
        # die mittlere Zeile blinkt
        try:
            self.LCD.clear()

            # Obere Zeile nur dann in Laufschrift, wenn es der Header ist. 
            self.LCD.write_single_line(self.disp_list[self.list_index-1], 0, blink=0, ls=((self.list_index-1) == 0))
            self.LCD.write_single_line(self.disp_list[self.list_index], 1, blink=1, ls=True)
            self.LCD.write_single_line(self.disp_list[self.list_index+1], 2, blink=0,ls=False)
        except IndexError:
            self.logger.error(f'{self.state}: IndexError _write_disp_list')
        except:
            self.logger.error(f'{self.state}: sonstiger Fehler _write_disp_list')


    def _write_help_list(self):
        # aktuell relevante Zeilen fuer die Hilfeanzeige darstellen
        # ACHTUNG: Nummerierung mit dem help_index beginnt an der obersten Zeile
        self.LCD.clear()
        self.LCD.write_single_line(self.help_list[self.help_index], 0, blink=0,ls=False)
        self.LCD.write_single_line(self.help_list[self.help_index+1], 1, blink=0, ls=True)
        self.LCD.write_single_line(self.help_list[self.help_index+2], 2, blink=0,ls=False)

    def list_user(self):
        # String mit einer Auflistung aller Benutzer erstellen, 
        # "A, B, C und D"
        shuffle(self.user)
        text=''
        for i,user in enumerate(self.user):
            if i == len(self.user)-1 and i>0:
                text = text + ' und ' + user 
            else:
                if (i > 0): 
                    text = text + ', ' + user 
                else:
                    text = text + ' ' + user 
        return text
    # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # ++++++++++++++++++++++++ allegemeine Zustandsfunktionen ++++++++++++++++++++
    # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

    def _load_helptext(self, helptextnum):
        # hilfetext laden, dan weiterreichen
        self.__load_helptext(copy.deepcopy(self.msg_dict[str(helptextnum+self.list_index)][self.lg]))

    def __load_helptext(self, text):
        # Basisfunktion, die jeden beliebigen Text in den Helptext formatiert
        self.help_list = split_lines(text, self.linewidth)
        print(self.help_list)
        self.add_footer_help()
        self.help_index = 0
        self.F_update_display = True
        self.logger.info(self.help_list)       

    def __load_errortext(self, text):
        # Basisfunktion, die jeden beliebigen Text in den Helptext formatiert
        text = text.replace('Traceback (most recent call last):', 'ERROR:        ')
        text = text.replace('File "/home/dietpi/hoerberry2/python_scripts/', 'File "')
        text = text.replace('\n', ' ')
        text = text.replace('  ', ' ')

        self.help_list = [text[i:i+self.linewidth] for i in range(0, len(text), self.linewidth)]

        self.add_footer_help()
        self.help_index = 0
        self.F_update_display = True
        self.logger.info(self.help_list)        

    def _run_helptext(self, exitstate):
        # Hilfetext anzeigen und Tastenreaktion

        # wenn nix passiert verbleiben wir hier
        self.newstate = self.state

        # Auf Tasten reagieren
        if self.F_button != self.BU_NONE:
            if self.F_button == self.BU_PREV:
                self.newstate = exitstate
                self.F_update_display = True
                self.logger.info(f'{self.state}: {self.F_button}, Hilfe verlassen?.')
                return
            # in der Liste scrollen
            elif self.F_button == self.BU_VOLUME_ROTATION:
                self._ch_help_index(self.N_button)
                self.F_update_display = True
            else:
                self.logger.info(f'{self.state}: {self.F_button}, wir reagieren nicht.')

        # Nur bei Verbleib aktualisieren. Bei Wechsel nach 710 hier das Update des 
        # Displays initialisieren
        if self.F_update_display and (self.newstate == self.state):
            self._write_help_list()
            self.F_update_display = False

    def _init_GPIO(self):
        # alle GPIO-Pins zuweisen
        GPIO.setmode(GPIO.BOARD)

        GPIO.setup(self.PINS[PIN_LED], GPIO.OUT, initial=GPIO.LOW)


        GPIO.setup(self.PINS[PIN_NEXT],GPIO.IN)
        GPIO.setup(self.PINS[PIN_PREV],GPIO.IN)

        # Pins der Tasten. Hier kam es beim Starten sporadisch zu Fehlern. Versuch, das durch warten zu beheben.
        try:
            GPIO.add_event_detect(self.PINS[PIN_NEXT], GPIO.FALLING, bouncetime=200)
            GPIO.add_event_callback(self.PINS[PIN_NEXT], self.OnNextButton)
        except RuntimeError:
            self.logger.error('runtime error add_event_detect PIN_NEXT')
            time.sleep(10)
            GPIO.add_event_detect(self.PINS[PIN_NEXT], GPIO.FALLING, bouncetime=200)
            GPIO.add_event_callback(self.PINS[PIN_NEXT], self.OnNextButton)
        try:
            GPIO.add_event_detect(self.PINS[PIN_PREV], GPIO.FALLING,bouncetime=200)
            GPIO.add_event_callback(self.PINS[PIN_PREV], self.OnPrevButton)
        except RuntimeError:
            self.logger.error('runtime error add_event_detect PIN_PREV')
            time.sleep(10)
            GPIO.add_event_detect(self.PINS[PIN_PREV], GPIO.FALLING,bouncetime=200)
            GPIO.add_event_callback(self.PINS[PIN_PREV], self.OnPrevButton)


    def _remove_GPIO(self):
        # Pins aufraumen
        # GPIO.cleanup() raumt alles auf, das geht nicht!
        GPIO.remove_event_detect(self.PINS[PIN_NEXT])
        GPIO.remove_event_detect(self.PINS[PIN_PREV])

    def _reset_info(self):
        # Inhalt von self.info zuruecksetzen (bis auf die Lautstaerke)
        self.info['state'] = 'stop'
        self.info['song_number'] = '0'
        self.info['elapsed_time'] = 0.0
        self.info['len_playlist'] = '-1'
        self.info['playlist'] = '0'
        self.info['duration'] = 0.0
        self.info['name'] = 'unbekannt'
          
    # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # ++++++++++++++++++++++++ Zustandsfunktionen +++++++++++++++++++++++++++++++
    # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

    def DO_ST_100(self):
        self.newstate = 150

        # hier WLAN einschalten, sonst bleibt das imme raus
        unblock_wifi()

        # komplette Settings laden (aktuelle Werte + Wertebereich )
        self.setup = load_file(self.cfg_gl['fname_setup'], self.cfg_gl['fname_dflt_setup'])
        self.logger.info('self.setup:')
        self.logger.info(self.setup)

        # Werte die via Editiermenue zugaenglich sind und eingestellt werden, aktuelle Werte!
        self.shuffle_step       = self._getval('shuffle_step')
        self.vol_max            = self._getval('vol_max')
        self.vol_step           = self._getval('vol_step')
        self.vol_step_Quick     = self._getval('vol_step_quick')
        self.BacklightMode      = self._getval('backlight')
        self.Timeout_backLight  = self._getval('timeout_backLight')
        self.timeout_shutdown   = self._getval('timeout_shutdown') * 60 
        self.lg                 = self._getval('language')
        self.wlansetting        = self._getval('wlan')

        self.wlan = True    # WLAN zu beginn aktiv
        # und noch die drei Zeitlimits...

        self.time_manager = TimeManager(self._getval('daily_limit')*60,   # im Editiermenue in Minuten, hier aber als Sekunden benoetigt
                                        self._getval('morning_limit'),
                                        self._getval('evening_limit'))
        # letztes Datum und abgespielte zeit laden                                        
        self.load_uptime()

        # UID-zu-Playlist-Verzeichnis laden
        self.uid_dict = load_file(self.cfg_gl['fname_uid_list'], self.cfg_gl['fname_dflt_uid_list'])


        # Timer mit den Ablaufzeiten initialisieren
        self.TIMER_DISPLAY = self.init_timer(self.ct_display_play)
        self.TIMER_BACKLIGHT = self.init_timer(self.Timeout_backLight)
        self.TIMER_RFID = self.init_timer(self.cycletime_RFID)
        self.TIMER_LED = self.init_timer(self.duration_LED_action)
        self.TIMER_AUTOSHUTDOWN = self.init_timer(self.timeout_shutdown)
        self.TIMER_MESSAGE = self.init_timer(self.message_display)
        self.TIMER_WLAN_CHECK = self.init_timer(self.cfg_gl['wlan_check'])
        # allgemeinen Timer zum Debuggen 
        self.TIMER_DEBUG = self.init_timer(self.message_display)
        self.TIMER_WLAN = self.init_timer(self.cfg_gl['wlanshutdown'])
        # Zaehler fuer das warten auf MPD
        self.init_counter=0


        self.logger.info(f'ct_display_play: {self.ct_display_play}')
        self.logger.info(f'Timeout_backLight: {self.Timeout_backLight}')
        self.logger.info(f'cycletime_RFID: {self.cycletime_RFID}')
        self.logger.info(f'duration_LED_action: {self.duration_LED_action}')
        self.logger.info(f'timeout_shutdown: {self.timeout_shutdown}')
        self.logger.info(f'message_display: {self.message_display}')
      
        
        # Dislay-Backlight gemaess setting schalten
        if self.BacklightMode  == self.BL_ON:
            self.LCD.setBacklight(GPIO.HIGH,0)
        else:
            self.LCD.setBacklight(GPIO.LOW,0)

        # Ansage nur beim Einschalten, denn dann ist noch kein laststate definiert
        if self.laststate == self.NO_NEWSTATE:
            # Begruessungsbildschirm an alle Benutzer
            msg = self.msg_dict["100"][self.lg]
            self._writeMessage(msg+self.list_user(), 0,3)
            # temporaer: IP beim Start anzeigen. WEnn die verfuegbar --> alles schon vor dem Netzwerk!
            self.logger.info(f'IP: {get_ip_address()}')

            # Begruessungsansage abspielen, einmalig wirklich nur beim Hochfaren, nicht nach dem Editiermenue
            # MPD bei Bedarf stoppen
            self.play_sound_msg('hello')
        else:
            # Anzeige entfernen
            self.LCD.clear()
            # Anzeigedaten loeschen
            self.LCD.clear_data()


    def DO_ST_150(self):
        self.newstate = 150

        # Musikwiedergabe fortsetzen, ohne laden der Playliste im Zustand 200
        if self.load_position():
            # Display mit aktuellem vol_max neu berechnen
            self._rescale_volume_disp()

            # Volumen auf self.info["volume"] setzen durch Volume-Aenderung von 0%
            self.adjust_volume(0)

            if self.info['playlist'] != self.NO_PLAYLIST:

                self.newstate = 160
                self.logger.info('150: Position erfolgreich geladen')
            else:
                self.newstate = self.ST_WAIT
                self.logger.info('150: keine Playlist geladen, nach WAIT')
        else:
            self.newstate = self.ST_WAIT
            self.logger.info('150: laden fehlgeschlagen, nach WAIT') 

        # unabhaengig vom vorherigen: wenn editstart erzwungen ist, gehen wir beim ersten Start in Editiermenu
        if self.editstart:
            self.editstart = False
            self.newstate = self.ST_EDIT_START
            self.logger.info('Start ins Editiermenue erzwungen')


    def DO_ST_160(self):
        self.newstate = 160

        try:
            if self._CheckConnection():
                self.newstate = 170
            else:
                self.init_counter += 1

        except mpd.ConnectionError:
            self.init_counter += 1
            
        self._writeMessage('O'*self.init_counter, 0,3)
        time.sleep(1)
        self.logger.info(f'{self.state}: Warten auf MPD')


    def DO_ST_170(self):
        if 'InternetRadio' in self.info['playlist']:
            # der 1300 muss durchlaufen werden, um die Internetverbindung abzufragen
            # Es muss keine Startposition geladen werden, daher tun wir so, als sei geradie
            # diese Karte angelegt worden.
            self.newstate = 1300
            self.playlist_request = self.info['playlist']
            return
        else: 
            # laden der alten Position abarbeiten
            self.newstate = 250

        # hier landet man nur, wenn die Verbindung OK ist. 
        try:
            self.cl.clear() 
        except:
            self.logger.error('Fehler: self.cl.clear() ')
            self.newstate = 400
            return

        try: 
            self.cl.load(self.info['playlist'])
        except:
            self.logger.error("Fehler: self.cl.load(self.info['playlist']) ")
            self.newstate = 400
            return

        try:
            if self.info['song_number'].isnumeric():
                self.cl.play(self.info['song_number'])
            else:
                self.cl.play()
        except:
            # wenn der richtige Titel nicht 
            self.logger.error("Fehler: self.cl.play(self.info['song_number']) ")
            self.logger.error(str(self.info))
            self.newstate = 400
            return

        try:
            self.cl.seekcur(self.info['elapsed_time'])
        except:
            # Fehler beim vorspulen koennen ignoriert werden, lediglich anzeigen!
            self.logger.error("Fehler: self.cl.seekcur(self.info['elapsed_time']) ")

    def DO_ST_200(self):
        # playliste laden und komplett im Display anzeigen, immer weiter nach 250!
        self.newstate = 250


        # abfrage, ob diese Playliste bereits abgespielt wird
        if self.playlist_request == self.info['playlist']:
            self.newstate = 250
            return

        # wird nicht bereits abgespielt, in MPD laden, sofern eine Verbindung besteht
        else:
            if self._CheckConnection():
                # Neue Playliste laden
                self.info['playlist'] = self.playlist_request

                self.cl.clear()            # aktuelle abspielliste loeschen, sonst wird die Playliste nur dazugeladen!
                self.cl.load(self.playlist_request)
                self.cl.play()

                # Kompletten Playlistennamen darstellen
                self._writeMessage(self.playlist_request)

                self.update_MPD_info()

            else: 
                # nochmal im naechsten zyklus versuchen
                self.newstate = 200
                return                

    def DO_ST_250(self):
        # kontinuierliches Abspielen der Musik, auf Tasten reagieren, Display aktualisieren,...
        # ohne Ereignis bleiben wir hier
        self.newstate = 250

        # Zeitenverwaltung, ggf. Musikwiedergabe sperren
        self.time_manager.count()
        self.time_manager.check_status()
        if self.time_manager.status != self.time_manager.status_ok:
            # irgendeine Abbruchbedingung ist erfuellt --> Abspielen beenden!

            # temporaere debugmeldungen:
            # self.logger.info('self.time_manager:')
            # self.logger.info(self.time_manager.morning_limit)
            # self.logger.info(self.time_manager.now)
            # self.logger.info(self.time_manager.get_uptime())
            # self.logger.info(self.time_manager.evening_limit)
            # self.logger.info(self.time_manager.now > self.time_manager.evening_limit)
            # self.logger.info(self.time_manager.sync)
            self.newstate = self.ST_BLOCKED
            return

        if self.F_RFID != self.NO_RFID:
            self.newstate = self.ST_LOADLIST
            return

        # automatischen Wechsel nach WAIT veranlassen, wenn die Playliste
        # durchgelaufen ist. Dass weiss man aber erst nach Abfrage von self.update_MPD_info().
        # Es ist moeglich, dass die Infoaktualisierung durch einen Tastendruck veranlasst wurde. Wenn
        # dann aber festgestellt wird, dass derzeit nix mehr abgespilt wird, ist der Tastendruck hinfaellig,
        # und wir brechen vorher in Richtung WAIT ab. 
        # Zeitkriterium fuer Displayupdate gilt nicht, wenn noch eine Message angezeigt wird
        if self.F_button != self.BU_NONE or (self.elapsed_time(self.TIMER_DISPLAY) and not self._validMessage()):
            self.update_MPD_info()
            self.F_update_display = True
            
            # normale Playliste
            if self.info['state'] != 'play':
                self.newstate = self.ST_WAIT
                return

        # jetzt erst die Tastereingabe verarbeiten
        if self.F_button != self.BU_NONE:
            self._CheckConnection()

            if self.F_button == self.BU_PREV:
                # Kommando an MPD schicken, dass Titel zurueck
                self.cl.previous()   
            elif self.F_button == self.BU_NEXT:
                # Titel vor
                self.cl.next()
            elif self.F_button == self.BU_PAUSE:
                # Pause ausloesen und in den Zustand ST_PAUSE wechseln
                self.cl.pause(1)
                self.LCD.quick_update_state('pause')
                self.newstate = self.ST_PAUSE
                # Displayupdate erzwingen
                self.F_update_display = True

            elif self.F_button == self.BU_PAUSE_ROTATION:
                # im Titel spulen. auch zum vorherigen Titel moeglich
                # Spulen zum naechsten Titel macht MPD automatisch...
                new_pos = float(self.info['elapsed_time']) + self.N_button*self.shuffle_step

                if (new_pos < 0.0) and self._check_prev():
                    # zum letzten Titel zurueckspringen, und dort passen shuffeln,
                    # sofern wir nicht beim ersten Titel sind. 
                    self.cl.previous()  
                    self.update_MPD_info()

                    self.cl.seekcur('{0:f}'.format(self.info['duration'] + new_pos) )
                else:
                    new_pos = max(0.0,new_pos)
                    # normales Spulen innerhalb des Titels
                    self.cl.seekcur('{0:f}'.format(new_pos) )

            elif self.F_button == self.BU_VOLUME_ROTATION:
                # Volume nach Anzahl der Schritte anpassen.
                print(self.N_button)
                # bei schneller Konpfdrehung deutlich mehr reagieren
                if abs(self.N_button) >= 3:
                    self.adjust_volume(self.N_button * self.vol_step_Quick)
                else:
                    self.adjust_volume(self.N_button * self.vol_step)

            self.update_MPD_info()

        # Displayupdate bei Anforderung
        if self.F_update_display or ((self.cur_disp_page == self.DISP_MESSAGE) and not self._validMessage()):
            self._writePlay()
            self.start_timer(self.TIMER_DISPLAY)
            self.F_update_display = False

    def DO_ST_300(self):
        # Eingangszustand Pause:
        # aktuelle Position MPD abspeichern und automatischen Shutdown einleiten
        self.save_current_position()
        self.start_timer(self.TIMER_AUTOSHUTDOWN)
        self.newstate = 350

        self.time_manager.stop()
        self.save_uptime()

    def DO_ST_350(self):
        # Wartezustand Pause:
        # auf PAUSE oder RFID warten
        self.newstate = 350

        if self.F_RFID != self.NO_RFID:
            self.newstate = self.ST_LOADLIST
            return

        # reduzierte Tastenreaktion
        if self.F_button == self.BU_PAUSE:
            # Pause beenden

            self._CheckConnection()
            self.cl.pause(0)

            self.LCD.quick_update_state('play')

            if 'InternetRadio' in self.info['playlist']:
                self.newstate = 1350
            else: 
                self.newstate = 250

        elif self.F_button == self.BU_VOLUME_ROTATION:
            # Latstaerke nur leiser stellen, display sofort anpassen
            if self.N_button < 0:
                self.adjust_volume(self.N_button * self.vol_step)
                self.LCD._write_volume(self.info['volume_disp'])

        # automatischen shutdown ueberwachen
        self.checkShutdown()
 

    def DO_ST_400(self):
        # Wartezustand WAIT
        # huebscheres Display, z,B. warte auf karte
        self.newstate = 450
       
        self.start_timer(self.TIMER_AUTOSHUTDOWN)

        self.time_manager.stop()
        self.save_uptime()

        self._reset_info()

        # Display schreiben, 
        self.LCD.clear()
        self._writeMessage(self.msg_dict["400"][self.lg])
        # todo: timer autoshutdown anzeigen...

    def DO_ST_450(self):
        # Wartezustand von WAIT
        # Auf RFID warten
        self.newstate = 450


        if self.F_RFID != self.NO_RFID:
            self.newstate = self.ST_LOADLIST

        # automatischen shutdown ueberwachen
        self.checkShutdown()
        

    def DO_ST_500(self):
        # LOADLIST, einmalig durchlaufen, automatischer Wechsel je nach RFID
        # keine RFID        --> ERROR
        # Mastercard        --> EDIT
        # Playliste läuft bereits --> PLAY, ohne Aktion
        # Playliste erkannt --> PLAY, Playlist laden
        # unbekannte RFID   --> zurueck zu laststate
        # danach die ausgelesene RFID zuruecksetzen auf NO_RFID



        # debug
        self.logger.debug(self.uid_dict)
        self.logger.info(self.F_RFID)

        if self.F_RFID in self.MasterCardID:
            self.newstate = self.ST_EDIT_START

        elif self.F_RFID in self.uid_dict.keys():
            # es ist ein Element der bekannten Playlisten
            self.playlist_request = self.uid_dict[self.F_RFID]

            # hier bestimmen, ob es ein Radio ist, ggf auch nur ein Update des bestehenden Status
            self.playlist_internetradio = self.playlist_request.endswith('InternetRadio')

            # neu laden, oder einfach fortsetzen
            if self.playlist_request == self.info['playlist']:
                self.newstate = self.laststate
                self._writeMessage(self.msg_dict["510"][self.lg],0,3)
            else:
                if self.playlist_internetradio:
                    self.newstate = self.ST_INTERNET_RADIO
                else:
                    self.newstate = self.ST_PLAY

        else:
            # unbekannte Karte 
            self.newstate = self.laststate
            self.logger.info("unbekannte PL:"+str(self.F_RFID))
            self._writeMessage(self.msg_dict["500"][self.lg])

        # hiermit ist diese Information verarbeitet und wird wieder zurueckgesetzt. 
        self.F_RFID = self.NO_RFID

    def DO_ST_600(self):
        # Eingangszustand Shutdown
        # Keine Reaktion auf die Buttons oder RFID mehr. 
        # Position speichern, Musik stoppen, runterfahren
        self.newstate = 650
        
        try:
            self.save_current_position()
            self.save_uptime()
        except:
            self.logger.error('Fehler Abspeichern aktuelle Position')


        # MPD anhalten
        self._CheckConnection()
        try:
            self.cl.stop()
        except mpd.base.ConnectionError:
            self.logger.info("mpd beim Runterfahren nicht mehr erreichbar")

        # Verabschiedung von allen Benutzern
        try:
            shuffle(self.user)
            msg = self.msg_dict["600"][self.lg]
            self._writeMessage(msg+self.list_user(), 0,3)
        except:
            self.logger.error('Fehler Anzeige Goodbye')

        # Goodbye-Ansage
        try:
            self.play_sound_msg('goodbye')
        except:
            self.logger.error('Fehler message googdbye')

        # selber den Shutdown des Raspi anstossen, nicht auf die ONOFF-shim warten
        subprocess.Popen(["sudo", "shutdown", "-h", "0"], stdout=subprocess.PIPE)

           
        self.F_shutdownCalled = True  

    def DO_ST_650(self):
        # Wartezustand shutdown, nix mehr machen
        # Keine Reaktion auf die Buttons oder RFID mehr.         
        self.newstate = 650

    def DO_ST_700(self):
        # Anzeige der Hilfe fuer das Editiermenue, im Hintergrund das Musikverzeichnis aktualisieren,
        # die Liste der Playlisten erstellen und die nicht zugeordneten Playlisten rausfiltern
        self.newstate = 705

        # Musikwiedergabe stoppen, aktuelle Position speichern
        if self.info['state'] == 'play':
            self._CheckConnection()
            self.cl.pause(1)
        self.save_current_position()

        self.time_manager.stop()
        self.save_uptime()

        # Zeit Displayupdate ateanpassen, wird im INIT wieder zurueckgesetzt
        self.TIMER_DISPLAY = self.init_timer(self.ct_display_edit)

        # Ab hier wird gearbeitet!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

        # Erster Schritt: 
        # veraltet und entfernt

        # Zweiter Schritt: Playlistendateien ohne Musik loeschen, 
        # fuer Musik ohne Playlistdatei diese erstellen
        # Die Playlisten auch fuer MPD aktualisieren: 
        # Titelverzeichnis mit dem Playlistennamen schreiben,
        # danach die Datenbank des MPC aktualisieren 
        update_all_playlists(self.cfg_gl['foname_music'],self.cfg_gl['foname_playlists']) 
        print('update_all_playlists done')

        # Dritter Schritt: Datei mit der Zuordnung {Playlistname : UID} laden
        self.playlists = load_file(self.cfg_gl['fname_pl'], self.cfg_gl['fname_dflt_pl'])



        all_pl = read_playlists(self.cfg_gl['foname_playlists'])
        old_keys = self.playlists.keys()
        # Vierter Schritt: vorhandene Playlistdateien (mit Musik) in die Liste
        # der Playlisten aufnehmen, aber al undefiniert
        for i in all_pl:
            if i not in old_keys:
                self.playlists[i] = 'undef'     

        # Fuenfter Schritt: veraltete Listenelemente, zu denen es keine Musik und
        # keine Playlistendatei mehr gibt entfernen
        tempdict = copy.deepcopy(self.playlists)
        for j in old_keys:
            if j not in all_pl:
                del tempdict[j]
                self.logger.info(f'Playliste {j} entfernt')
        self.playlists = copy.deepcopy(tempdict)

        # Index nur hier wirklich initialisieren!
        self.list_index = 1

    def DO_ST_705(self):
        self.newstate = 710
        # Displayanzeige
        # Elemente fuer die Listenanzeige laden, Displayupdate anstossen
        self.disp_list = copy.deepcopy(self.msg_dict["700"][self.lg])
        # Kopfzeile kriegt die IP mit rangehaengt: (auf der zweiten Seite)
        self.disp_list[0] = self.disp_list[0].center(self.linewidth) + get_ip_address() 

        # Nummerierung, aber nicht fuer den Titel
        self.disp_list[1::] = add_numbering(self.disp_list[1::])
        self.disp_list.append(self.generate_footer(prev='EXIT'))
        self.F_update_display = True

    def DO_ST_710(self):
        # Liste der Menues anzeigen
        self.newstate = 710

        # Liste anpassen, in Untermenues gehen
        if self.F_button != self.BU_NONE:
            if self.F_button == self.BU_PAUSE:
                # anhand vom aktuellen Element zum naechsten Zustand
 
                if self.list_index == 1: 
                    self.newstate = 800   
                elif self.list_index == 2: 
                    # Musik und Displayeinstellungen 
                    self.newstate = 900   
                elif self.list_index == 3: 
                    # allgemeine Einstellungen 
                    self.newstate = 1000   

            elif self.F_button == self.BU_PREV:
                self.newstate = 1100   
                return

            elif self.F_button == self.BU_NEXT:
                # zur Hilfe gehen
                self.newstate = 790  

            # in der Liste scrollen
            elif self.F_button == self.BU_VOLUME_ROTATION:
                self._ch_index(self.N_button)
                self.F_update_display = True

        # Anzeige Editiermenue ins Display bringen
        if self.F_update_display:
            self._write_disp_list()
            self.F_update_display = False

    def DO_ST_790(self):
        # Hilfedatei laden, Position initialisieren
        self.newstate = 795
        self._load_helptext(700)

    def DO_ST_795(self):
        # Laufschrift wiedergeben, bis es mit PAUSE oder RFID weitergeht, Oder zur anderen Anzeige springen
        self._run_helptext(705)

    def DO_ST_800(self):
        # Menue: Playlistenzuordnung
        # Liste leer: sofort weiter
        # sonst: Hilfe anzeigen, in das Editiermenue weitergehen
        self.newstate = 805
        self.list_index = 1

    def DO_ST_805(self):
        self.newstate = 810
        # Displayanzeige
        # Elemente fuer die Listenanzeige laden, Displayupdate anstossen
        self.disp_list = copy.deepcopy(self.msg_dict["800"][self.lg])
        # Nummerierung, aber nicht fuer den Titel
        self.disp_list[1::] = add_numbering(self.disp_list[1::])
        self.disp_list.append(self.generate_footer())
        self.F_update_display = True


    def DO_ST_810(self):
        # Listenanzeige der Untermenues:
        # - undef Playlisten zuordnen
        # - Playlisten ändern
        # - Karten kontrollieren
        self.newstate = 810

        # Liste anpassen, in Untermenues gehen
        if self.F_button != self.BU_NONE:
            if self.F_button == self.BU_PAUSE:
                # anhand vom aktuellen Element zum naechsten Zustand
                if self.list_index == 1: 
                    self.newstate = 820   
                elif self.list_index == 2: 
                    self.newstate = 830   
                elif self.list_index == 3: 
                    self.newstate = 840   

            elif self.F_button == self.BU_PREV:
                # zum vorherigen Menue zurueck, an der richtigen Stelle rauskommen!
                self.newstate = 705 
                self.list_index = 1 
                self.F_update_display = True
                return

            elif self.F_button == self.BU_NEXT:
                # zur Hilfe gehen
                self.newstate = 890  

            # in der Liste scrollen
            elif self.F_button == self.BU_VOLUME_ROTATION:
                self._ch_index(self.N_button)
                self.F_update_display = True

        # Nur bei Verbleib aktualisieren. Bei Wechsel nach 710 wurde hier das Update des 
        # Displays initialisiert
        if self.F_update_display and (self.newstate == self.state):
            self._write_disp_list()
            self.F_update_display = False

    def DO_ST_820(self):
        # Undef-Playlisten: liste erstellen
        self.newstate = 825

        self.undef_playlists = {}
        for key,item in self.playlists.items():
            if not self._isUID(item):
                self.undef_playlists[key] = item
                self.logger.info('no UID: {}'.format(key))
        
        if len(self.undef_playlists) > 0:
            self.mode_keys = sorted(self.undef_playlists)
        else: 
            # anzeigen, dass keine da ist
            self.mode_keys = ['no undef Playlists available']
 
        # Displayliste erstellen:
        # Header
        # Liste der Playlisten
        # Fusszeile
        self.disp_list = [copy.deepcopy(self.msg_dict["820"][self.lg])]
        self.disp_list = self.disp_list + self.mode_keys
        self.disp_list.append(self.generate_footer(pause=False,next=False))
        self.list_index = 1
        self.F_update_display = True   
        self.logger.info(f'{self.state}: '+str(self.disp_list))     

    def DO_ST_825(self):
        # Liste der nicht zugeordneten anarbeiten, auf RFID reagieren
        self.newstate = 825

        # zurueck zum letzten Menue
        if self.F_button == self.BU_PREV:
            # zurueck nach 805
            self.newstate = 805
            self.F_update_display = True
            self.list_index = 1
            return

        # in der Liste scrollen
        if self.F_button == self.BU_VOLUME_ROTATION:
            self._ch_index(self.N_button)
            self.F_update_display = True

        # jede RFID, die kommt, zuweisen
        if self.F_RFID in self.MasterCardID:
            return
        elif (self.F_RFID != self.NO_RFID) and (self.mode_keys != ['no undef Playlists available']):
            # nur wenn es wirklich zu aktualisierende Playlisten gibt!
            # irgendeine RFID wurde angelegt --> Zuordnung aktualisieren
            # alte Anzeige der UID loeschen und neue Anzeige initiieren
            self.playlists[self.mode_keys[self.list_index-1]] = self.F_RFID 
            self.undef_playlists[self.mode_keys[self.list_index-1]] = self.F_RFID 
            self.logger.info('added:')
            self.logger.info(self.mode_keys[self.list_index-1])
            self.logger.info(self.undef_playlists)
            # aktuelle mittlere Zeile mit der Nummer ueberschreiben
            self.LCD.write_uid(self.F_RFID, 1)
            # Zeichen zur Markierung voranstellen, dass der schon versorgt ist. 
            if self.disp_list[self.list_index][0] != '+':
                self.disp_list[self.list_index] = '+'+self.disp_list[self.list_index]
            time.sleep(self.sleep_uid_update)
            self.F_update_display = True   


        # Anzeige Editiermenue ins Display bringen
        if self.F_update_display and (self.state==self.newstate):
            self._write_disp_list()
            self.F_update_display = False

    def DO_ST_830(self):
        # Alle Playlisten: liste der zugeordneten Playlisten erstellen
        # 
        self.newstate = 835

        # nur die zugeordneten Playlisten laden
        self.def_playlists = {}
        for key,item in self.playlists.items():
            if self._isUID(item):
                self.def_playlists[key] = item

        self.logger.info(self.mode_keys)
        
        if len(self.def_playlists) > 0:
            self.mode_keys = sorted(self.def_playlists)
        else: 
            # anzeigen, dass keine da ist
            self.mode_keys = ['no Playlists available']
 
        # Displayliste erstellen:
        # Header
        # Liste der Playlisten
        # Fusszeile
        self.disp_list = [copy.deepcopy(self.msg_dict["830"][self.lg])]
        self.disp_list = self.disp_list + self.mode_keys
        self.disp_list.append(self.generate_footer(pause=False,next=False))
        self.list_index = 1
        self.F_update_display = True  

    def DO_ST_835(self):
        # Liste der nicht zugeordneten anarbeiten, auf RFID reagieren
        self.newstate = 835

        # zurueck zum letzten Menue
        if self.F_button == self.BU_PREV:
            # zurueck nach 805
            self.newstate = 805
            self.F_update_display = True
            self.list_index = 2
            return

        # in der Liste scrollen
        if self.F_button == self.BU_VOLUME_ROTATION:
            self._ch_index(self.N_button)
            self.F_update_display = True
            self.logger.info('drehung erkannt')

        # jede RFID, die kommt, zuweisen
        if self.F_RFID in self.MasterCardID:
            return
        elif self.F_RFID != self.NO_RFID:
            # irgendeine RFID wurde angelegt --> Zuordnung aktualisieren
            # alte Anzeige der UID loeschen und neue Anzeige initiieren
            # "-1" wegen der Kopfzeile. self.list_index zaehlt die Elemente der
            # Displayliste, die Inhaltnummerierung liegt aber bei -1.
            self.playlists[self.mode_keys[self.list_index-1]] = self.F_RFID 
            self.logger.info(self.mode_keys[self.list_index-1])
            self.logger.info(self.playlists[self.mode_keys[self.list_index-1]])
            # aktuelle mittlere Zeile mit der Nummer ueberschreiben
            self.LCD.write_uid(self.F_RFID, 1)
            time.sleep(self.sleep_uid_update)
            self.F_update_display = True   

        # Anzeige Editiermenue ins Display bringen
        if self.F_update_display and (self.state==self.newstate):
            self._write_disp_list()
            self.F_update_display = False

    def DO_ST_840(self):
        # ST_EDIT_CHECK: Nur das Auslesen von Karten, zum Ueberpruefen
        self.newstate = 845

        self.temp_uid_dict = {}
        for key, val in self.playlists.items():
            self.temp_uid_dict[val]=key

        # Hier 2 Zeilen, damit ist das eine Liste!!! Muss nicht extra in eine UMgewandelt werden
        self.disp_list = copy.deepcopy(self.msg_dict["840"][self.lg])
        self.disp_list.append(self.generate_footer(updown=False,pause=False,next=False))
        self.list_index = 1
        self.start_timer(self.TIMER_MESSAGE)
        self._write_disp_list()

    def DO_ST_845(self):
        # Playliste und RFID anzeigen, sofern eine kommt
        self.newstate = 845

        # zurueck zum letzten Menue
        if self.F_button == self.BU_PREV:
            # zurueck nach 805
            self.newstate = 805
            self.F_update_display = True
            self.list_index = 3
            return

        if self.F_RFID in self.MasterCardID:
            self.LCD.clear_line(1)
            self.LCD.clear_line(2)
            time.sleep(self.sleep_uid_update)
            self.LCD.write_lines(self.msg_dict["845_master"][self.lg], 1, 2)
            self.start_timer(self.TIMER_MESSAGE)
            time.sleep(self.sleep_uid_display)
        elif self.F_RFID != self.NO_RFID:
            # irgendeine RFID wurde angelegt --> anzeigen!
            self.LCD.clear_line(1)
            self.LCD.clear_line(2)
            time.sleep(self.sleep_uid_update)
            if self.F_RFID in self.temp_uid_dict.keys():
                self.LCD.write_lines(self.temp_uid_dict[self.F_RFID], 1, 2)  
            else:
                self.LCD.write_lines(self.msg_dict["845"][self.lg], 1, 2)
            self.start_timer(self.TIMER_MESSAGE)
            time.sleep(self.sleep_uid_display)

        # nach langer Zeit das Display zuruecksetzen
        if self.elapsed_time(self.TIMER_MESSAGE):
            self._write_disp_list()
            self.start_timer(self.TIMER_MESSAGE)

    def DO_ST_890(self):
        # Hilfedatei laden, Position initialisieren
        self.newstate = 895
        self._load_helptext(800)

    def DO_ST_895(self):
        # Hilfetext anzeigen, Velassen der Hilfe nach 805
        self._run_helptext(805)
        

    def DO_ST_900(self):
        # Einstellungen
        self.newstate = 910

        self._index_key = 0
        self.mode_keys = sorted(self.setup)

        # Disp-list erstellen
        self.disp_list = [copy.deepcopy(self.msg_dict["900"][self.lg])]
        self.disp_list += self.mode_keys
        self.disp_list[1::] = add_numbering(self.disp_list[1::])
        self.disp_list.append(self.generate_footer())
        self.F_update_display = True
        self.list_index = 1

    def DO_ST_910(self):
        # Listenanzeige der Einstellungskategorien
        self.newstate = 910

        # Liste anpassen, in Untermenues gehen
        if self.F_button != self.BU_NONE:
            if self.F_button == self.BU_PAUSE:
                # zum Einstellen des aktuellen Elements
                self.newstate = 950

            elif (self.F_button == self.BU_PREV):
                # zum vorherigen Menue zurueck, an der richtigen Stelle rauskommen!
                self.newstate = 705 
                self.list_index = 2
                self.F_update_display = True
                return

            elif self.F_button == self.BU_NEXT:
                # zur Hilfe gehen
                self.newstate = 990  

            # in der Liste scrollen
            elif self.F_button == self.BU_VOLUME_ROTATION:
                self._ch_index(self.N_button)
                self.F_update_display = True

        # Nur bei Verbleib aktualisieren. Bei Wechsel nach 710 wurde hier das Update des 
        # Displays initialisiert
        if self.F_update_display and (self.newstate == self.state):
            self._write_disp_list()
            self.F_update_display = False

    def DO_ST_950(self):
        # Anzeigetext fuer das aktuelle Element erzeugen
        self.newstate = 955
        self._index_key = self.list_index - 1

        # Kopfzeile mit dem Namen des Einstelleigenschaft
        self.LCD.write_single_line(self.disp_list[self.list_index], 0)
        # Mittlere Zeile mit den Werten
        self.LCD.write_single_line(self.get_val_string(), 1)
        # Fusszeile
        self.LCD.write_single_line(self.generate_footer(pause='OK', updown=False,leftright=True), 2)

    def DO_ST_955(self):
        # Einstellungen der jeweiligen Kategorie vornehmen, Wert veraendern
        self.newstate = 955

        # Tastenreaktion: PREV geht zurueck nach EDIT_PAIR, Pause macht das auch, als "Bestaetigen"
        # (--> Pause nur wegen konssitenter Bedienung mit dem restlichen Menue)
        if (self.F_button == self.BU_PREV) or (self.F_button == self.BU_PAUSE):
            self.newstate = 910   
            self.F_update_display = True
            return
        elif self.F_button == self.BU_NEXT:
            # zur Hilfe gehen
            self.newstate = 958 
        # Zahlenwert fuer das aktuele Element veraendern
        elif self.F_button == self.BU_VOLUME_ROTATION:
            self._ch_val(self.N_button)
            self.F_update_display = True


        if self.F_update_display and (self.newstate == self.state):
            self.LCD.write_single_line(self.get_val_string(), 1)
            self.F_update_display = False

    def DO_ST_958(self):
        # Hilfedatei laden, Position initialisieren
        self.newstate = 959
        self._load_helptext(900)

    def DO_ST_959(self):
        # Hilfetext anzeigen
        self._run_helptext(950)

    def DO_ST_990(self):
        # Hilfedatei laden, Position initialisieren
        self.newstate = 995
        self._load_helptext(900)

    def DO_ST_995(self):
        # Hilfetext anzeigen
        self._run_helptext(910)

    def DO_ST_1000(self):
        # allgemeine Einstellungen

        self.newstate = 1005
        self.list_index = 1

    def DO_ST_1005(self):
        self.newstate = 1010
        # Displayanzeige
        # Elemente fuer die Listenanzeige laden, Displayupdate anstossen
        self.disp_list = copy.deepcopy(self.msg_dict["1000"][self.lg])
        # Nummerierung, aber nicht fuer den Titel
        self.disp_list[1::] = add_numbering(self.disp_list[1::])
        self.disp_list.append(self.generate_footer())
        self.F_update_display = True

    def DO_ST_1010(self):
        # Listenanzeige der Untermenues:
        # - IP-anzeigen, 
        # - Mastercards
        # - WLAN (Name+Passwort)  
        # - resetFactorySettings  default-Dateien anlegen, im Felerfall diese im Init laden
        # - Update mit Guthub
        # - Nutzerstatistik
        self.newstate = 1010

        # Liste anpassen, in Untermenues gehen
        if self.F_button != self.BU_NONE:
            if self.F_button == self.BU_PAUSE:
                # anhand vom aktuellen Element zum naechsten Zustand
                if self.list_index == 1: 
                    # Mastercad hinzufuegen 
                    self.newstate = 1020   
                elif self.list_index == 2:
                    # WLAN einstelen
                    self.newstate = 1030   
                elif self.list_index == 3:
                    # - lokale Settingdateien loeschen! 
                    # - Kartenzuordnung entfernen
                    # - Masterkarten loeschen
                    # - History loeschen
                    self.newstate = 1050   
                elif self.list_index == 4:
                    # Updates suchen
                    self.newstate = 1060   
                elif self.list_index == 5:
                    # Nutzerstatistik
                    self.newstate = 1070   
                elif self.list_index == 6:
                    # IP-Addresse
                    self.newstate = 1080   

            elif self.F_button == self.BU_PREV:
                # zum vorherigen Menue zurueck, an der richtigen Stelle rauskommen!
                self.newstate = 705 
                self.list_index = 3
                self.F_update_display = True
                return

            elif self.F_button == self.BU_NEXT:
                # zur Hilfe gehen
                self.newstate = 1090  

            # in der Liste scrollen
            elif self.F_button == self.BU_VOLUME_ROTATION:
                self._ch_index(self.N_button)
                self.F_update_display = True

        # Nur bei Verbleib aktualisieren. Bei Wechsel nach 710 wurde hier das Update des 
        # Displays initialisiert
        if self.F_update_display and (self.newstate == self.state):
            self._write_disp_list()
            self.F_update_display = False

    def DO_ST_1020(self):
        # Mastercard-Verwaltung

        self.newstate = 1025
        self.LCD.clear()
        self.LCD.clear_data()
        self.LCD.write_single_line(self.msg_dict["1020"][self.lg], 0)
        self.LCD.write_single_line(self.msg_dict["1021"][self.lg], 1)
        self.LCD.write_single_line(self.generate_footer(pause=False, next=False, updown=False), 2)
              
        return

    def DO_ST_1025(self):
        # Mastercar hinzufuegen
        self.newstate = 1025

        if (self.F_RFID != self.NO_RFID):
            if self.F_RFID in self.MasterCardID:
                # bereits als Mastercard registriert?
                self.LCD.write_single_line(self.msg_dict["1022"][self.lg], 1)

            elif self.F_RFID in self.uid_dict.keys():
                # bereits als Playlist hinterlegt? 
                self.LCD.write_single_line(self.msg_dict["1023"][self.lg], 1)

            else:
                self.MasterCardID.append(self.F_RFID)
                self.LCD.write_single_line(self.msg_dict["1024"][self.lg], 1)
            # bestimmte Zeit anzeigen, dann wieder loeschen

        if self.F_button == self.BU_PREV:
            # zum vorherigen Menue zurueck, an der richtigen Stelle rauskommen!
            self.newstate = 1005 
            self.list_index = 1
            self.F_update_display = True
            return

    def DO_ST_1030(self):
        # WLAN einstellen:
        # - WLAN-Name eingeben, 
        # - WLAN-Passwort eingeben
        self.newstate = 1031

        # Text-Eingabefeld resetten
        self.input.clear_all()

        self.LCD.clear()
        self.LCD.clear_data()
        self.LCD.write_single_line(self.msg_dict["1031"][self.lg], 0)
        # mittlere Zeile fuer den Input:
        self.LCD.write_single_line(self.input.get_display_string(), 1)

        self.LCD.write_single_line(self.generate_footer(pause="SW", next="OK", updown=True, leftright=False), 2)

    def DO_ST_1031(self):
        # Eingabemaske des WLAN-Namens
        self.newstate = 1031

        # Eingabe abhandeln
        if self.F_button != self.BU_NONE:
            # Zeichentabelle wechseln
            if self.F_button == self.BU_PAUSE:
                # Wenn der Button schnell betaetigt wird --> mehrfach ausfuehren!
                for i in range(self.N_button):
                    self.input.change_charset()
            
            # Zeichen durchgehen
            if self.F_button == self.BU_PAUSE_ROTATION:
                self.input.change_index(self.N_button)
            
            # Curserposition wechseln
            if self.F_button == self.BU_VOLUME_ROTATION:
                if self.N_button > 0:
                    for i in range(self.N_button):
                        self.input.cursor_right()
                else:
                    # self.N_button ist negativ!!!
                    for i in range(-self.N_button):
                        self.input.cursor_left()

            # Eingabe fertig, weiter
            if self.F_button == self.BU_NEXT:
                self.newstate = 1032
                # Eingabe auslesen und speichern
                self.wlaninfo[0] = self.input.get_string()
                # input resetten
                self.input.clear_all()

            # Abbruch
            if self.F_button == self.BU_PREV:
                # zum vorherigen Menue zurueck, an der richtigen Stelle rauskommen!
                self.newstate = 1005 
                self.list_index = 2
                self.F_update_display = True
                return               

            # Bei Eingabe immer das Display updaten!
            self.LCD.write_single_line(self.input.get_display_string(), 1)

        # ohne Eingabe trotzdem das Display updaten?
        else:
            self.LCD.write_single_line(self.input.get_display_string(), 1)


    def DO_ST_1032(self):
        # WLAN einstellen:
        # - WLAN-Passwort eingeben
        self.newstate = 1033

        # Text-Eingabefeld resetten
        self.input.clear_all()

        self.LCD.clear()
        self.LCD.clear_data()
        self.LCD.write_single_line(self.msg_dict["1033"][self.lg], 0)
        # mittlere Zeile fuer den Input:
        self.LCD.write_single_line(self.input.get_display_string(), 1)
        # Hilfezeile anders als sonst
        self.LCD.write_single_line(self.generate_footer(pause="SW", next="OK", updown=True, leftright=False), 2)

    def DO_ST_1033(self):
        # Eingabemaske des WLAN-Passwortes
        self.newstate = 1033

        # Eingabe abhandeln
        if self.F_button != self.BU_NONE:
            # Zeichentabelle wechseln
            if self.F_button == self.BU_PAUSE:
                self.input.change_charset()
            
            # Zeichen durchgehen
            if self.F_button == self.BU_PAUSE_ROTATION:
                self.input.change_index(self.N_button)
            
            # Curserposition wechseln
            if self.F_button == self.BU_VOLUME_ROTATION:
                if self.N_button > 0:
                    for i in range(abs(self.N_button)):
                        self.input.cursor_right()
                else:
                    for i in range(abs(self.N_button)):
                        self.input.cursor_left()

            # Eingabe fertig, weiter
            if self.F_button == self.BU_NEXT:
                self.newstate = 1035
                # Eingabe auslesen und speichern
                self.wlaninfo[1] = self.input.get_string()
                # input resetten
                self.input.clear_all()

            # Abbruch
            if self.F_button == self.BU_PREV:
                # zum vorherigen Menue zurueck, an der richtigen Stelle rauskommen!
                self.newstate = 1005 
                self.list_index = 2
                self.F_update_display = True
                return               

            # Bei Eingabe immer das Display updaten!
            self.LCD.write_single_line(self.input.get_display_string(), 1)

        # ohne Eingabe trotzdem das Display updaten?
        else:
            self.LCD.write_single_line(self.input.get_display_string(), 1)            

    def DO_ST_1035(self):
        # config anpassen!
        self.newstate = 1039

        print("Hier jetzt WLAN-Passwort hinterlegen!")
        print(self.wlaninfo[0])
        print(self.wlaninfo[1])

        import pw_generator

        # verschluesseltes Passwort mit wpa_passphrase erzeugen und 
        # nach /etc/wpa_supplicant/wpa_supplicant.conf schreiben
        pw_generator.add_wlan(self.wlaninfo[0], self.wlaninfo[1])
        self.logger.info('WLAN-Passowort hinterlegt')

        # Ausgabe von der Konsole nach der Info parsen, config.txt bearbeiten und speichern
        self.wlaninfo = ['','']
        self.input.clear_all()

        # Display anpasse: mitteilen, dass Aenderung erfolgreich war, Quittierung verlangen
        self.LCD.clear()
        self.LCD.clear_data()
        self.LCD.write_single_line(self.msg_dict["1035"][self.lg], 0)
        self.LCD.write_single_line(self.generate_footer(next=False, updown=False), 2)


        # WLAN-Name und Passwort abfragen --> Eingabe Zahlen un dBuchstaben mit Drehdrück...
        # --> Paswort verschluesseln
        # --> Ergebnisstring parsen und an sudo nano /etc/wpa_supplicant/wpa_supplicant.conf anhaengen 

    def DO_ST_1039(self):
        # bestaetigung, dass WLAN-Paswort hinterlegt wurde, auf Quittierung warten
        self.newstate = 1039

        if (self.F_button == self.BU_PREV) or (self.F_button == self.BU_PAUSE):
            # zum vorherigen Menue zurueck, an der richtigen Stelle rauskommen!
            self.newstate = 1005 
            self.list_index = 2
            self.F_update_display = True    

    def DO_ST_1050(self):
        # TODO: zu loeschende Datensaetze auswaehlbar gestalten?
        # folgende Dateien loeschen:
        # - Liste der Mastercard
        # - Playlistenzuordnung
        # - settings
        # - uptime
        self.LCD.clear()
        self.LCD.clear_data()

    
        self.LCD.write_lines(self.msg_dict["1050"][self.lg], 0, 2)
        self.LCD.write_single_line(self.generate_footer(prev='HELP', updown=False, pause='NO', next='OK'), 2)
        self.newstate = 1051


    def DO_ST_1051(self):
        # auf das quittieren warten: Zurueck, weiter, oder die Hilfe
        # zurueck zum letzten Menue
        self.newstate = 1051

        if self.F_button == self.BU_PAUSE:
            # zurueck nach 1005
            self.newstate = 1005
            self.F_update_display = True
            self.list_index = 3
            return

        elif self.F_button == self.BU_NEXT:
            # Bestaetigt
            self.newstate = 1055
            self.F_update_display = True
            self.list_index = 3
            return
        elif self.F_button == self.BU_PREV:
            # zur Hilfe gehen
            self._load_helptext(1000)
            self.newstate = 1059  

    def DO_ST_1055(self):
        # eigentliches Loeschen der Dateien
        for f_name in ['fname_setup', 'fname_pl','fname_uid_list','fname_uptime','fname_last_pos']:

            try:
                subprocess.call(f'sudo rm {self.cfg_gl[f_name]}', shell=True)
            except:
                self.logger.error(f'Entfernen gescheitert: {f_name}')


        # Bestaetigung senden, dass gerade alles zurueckgesetzt wurde    
        self.LCD.clear()
        self.LCD.clear_data()
        self.LCD.write_lines(self.msg_dict["1055"][self.lg], 0, 2)
        self.LCD.write_single_line(self.generate_footer(next=False, prev=False,updown=False, pause='OK'), 2)
        self.newstate = 1056

    def DO_ST_1056(self):
        # Nach dem Quittieren zurueck eine Ebene hoeher
        self.newstate = 1056

        if self.F_button == self.BU_PAUSE:
            self.newstate = 1005
            self.F_update_display = True
            self.list_index = 3

    def DO_ST_1059(self):
        self._run_helptext(1050)

    def DO_ST_1060(self):
        # Information des letzten Commits als Hilfetext anzeigbaer gestalten?
        # ins Verzeichnis des Repositories wechseln
        os.chdir(self.cfg_gl['foname_repo'])

        p = subprocess.Popen(["sudo", "git", "pull", "origin", "main"], stdout=subprocess.PIPE)

        return_stuff = p.communicate()
        ascii_str = return_stuff[0].decode('ascii')
        self.logger.info(ascii_str)

        # aktuele revisionsnummer erfragen
        p = subprocess.Popen(["git", "rev-parse", "--short", "HEAD"], stdout=subprocess.PIPE)
        return_stuff = p.communicate()
        rev_num = return_stuff[0].decode('ascii')
        self.logger.info(rev_num)

        self.LCD.clear()
        self.LCD.clear_data()
        # Rueckgabe von git 1:1 auf das Display zaubern. 
        self.LCD.write_lines(ascii_str, 0, 1)
        self.LCD.write_single_line(f"Rev: {rev_num}", 1)
        self.LCD.write_single_line(self.generate_footer(next="HELP", prev=False,updown=False, pause='OK'), 2)

        self.newstate = 1065

    def DO_ST_1065(self):
        # Nach dem Quittieren zurueck eine Ebene hoeher
        self.newstate = 1065

        if self.F_button == self.BU_PAUSE:
            self.newstate = 1005
            self.F_update_display = True
            self.list_index = 4

        elif self.F_button == self.BU_NEXT:
                # zur Hilfe gehen
            p = subprocess.Popen(["git", "shortlog"], stdout=subprocess.PIPE)
            return_stuff = p.communicate()
            ascii_str = return_stuff[0].decode('utf-8')
            lines = ascii_str.split('\n')
            self.logger.info(lines)

            # am Ende sind 2 Leerzeilen, die davor ist der letzte aktuelle Commit
            if len(lines) > 2:
                self.__load_helptext(lines[-3])
            else:
                self.__load_helptext("no help available")

            self.newstate = 1069   

    def DO_ST_1069(self):
        # Gleich zurueck in die Hauptebene
        self._run_helptext(1005)

    def DO_ST_1070(self):
        # Nutzerstatistik anzeigen
        self.newstate = 1075

        # Nutzerstatistik laden
        data = load_file(self.cfg_gl['fname_uptime'], self.cfg_gl['fname_dflt_uptime'])

        self.disp_list = [copy.deepcopy(self.msg_dict["1070"][self.lg])]
        # jeden Eintrag formattiert hinzufuegen
        for i in sorted(data, reverse=True, key=days_since):
            date = i.split('-')

            hh = data[i]//3600
            sec = data[i] % 3600
            min = sec // 60
            sec = sec % 60
            # dd.mm.  hh:mm:ss
            self.disp_list.append('{:02d}.{:02d}.  {:02d}:{:02d}:{:02d}'.format(int(date[2]), int(date[1]), hh, min, sec )   )
        self.disp_list.append(self.generate_footer(pause=False,next=False))
        self.list_index = 1
        self.F_update_display = True  

    def DO_ST_1075(self):
        self.newstate = 1075

        # zurueck zum letzten Menue
        if self.F_button == self.BU_PREV:
            # zurueck nach 1005
            self.newstate = 1005
            self.F_update_display = True
            self.list_index = 5
            return

        # in der Liste scrollen
        if self.F_button == self.BU_VOLUME_ROTATION:
            self._ch_index(self.N_button)
            self.F_update_display = True            

        # Anzeige Editiermenue ins Display bringen
        if self.F_update_display and (self.state==self.newstate):
            self._write_disp_list()
            self.F_update_display = False


    def DO_ST_1080(self):
        # IP anzeigen
        self.newstate = 1085

        self.LCD.clear()
        self.LCD.clear_data()
        self.LCD.write_single_line(self.msg_dict["1080"][self.lg], 0)

        self.logger.info("output IP:"+get_ip_address())
        self.LCD.write_single_line(get_ip_address(), 1)
        self.LCD.write_single_line(self.generate_footer(pause=False, next=False, updown=False), 2)

    def DO_ST_1085(self):
        # IP weiter anzeigen, auf Abbruch warten 
        self.newstate = 1085

        # zurueck zum letzten Menue
        if self.F_button == self.BU_PREV:
            # zurueck nach 1005
            self.newstate = 1005
            self.F_update_display = True
            self.list_index = 6
            return

    def DO_ST_1090(self):
        # Hilfeanzeige Add_Mastercard  
        self._load_helptext(1000)
        self.newstate = 1095

    def DO_ST_1095(self):
        # Hilfeanzeige Add_Mastercard  
        self._run_helptext(1005)

    def DO_ST_1100(self):
        # Editiermenue Verlassen, mit oder ohne Speichern
        self.newstate = 1105
        # Index nur hier wirklich initialisieren!
        self.list_index = 1

    def DO_ST_1105(self):
        self.newstate = 1110
        # Displayanzeige
        # Elemente fuer die Listenanzeige laden, Displayupdate anstossen
        self.disp_list = copy.deepcopy(self.msg_dict["1100"][self.lg])
        # Nummerierung, aber nicht fuer den Titel
        self.disp_list[1::] = add_numbering(self.disp_list[1::])
        self.disp_list.append(self.generate_footer())
        self.F_update_display = True

    def DO_ST_1110(self):
        # Liste der Menues anzeigen
        self.newstate = 1110

        # Liste anpassen, in Untermenues gehen
        if self.F_button != self.BU_NONE:
            if self.F_button == self.BU_PAUSE:
                # Zur Bestaetigung gehen
                self.newstate = 1120   
 

            elif self.F_button == self.BU_PREV:
                # zurueck ins Hauptmeue
                self.newstate = 705 
                self.list_index = 1 
                self.F_update_display = True                
                return

            elif self.F_button == self.BU_NEXT:
                # zur Hilfe gehen
                self.newstate = 1190  

            # in der Liste scrollen
            elif self.F_button == self.BU_VOLUME_ROTATION:
                self._ch_index(self.N_button)
                self.F_update_display = True

        # Anzeige Editiermenue ins Display bringen
        if self.F_update_display:
            self._write_disp_list()
            self.F_update_display = False

    def DO_ST_1120(self):
        # Bestaetigung der Auswahl
        self.newstate = 1125
        self.LCD.write_single_line(self.disp_list[self.list_index], 0)
        self.LCD.write_single_line(self.msg_dict["1120"][self.lg], 1)
        self.LCD.write_single_line('BACK          OK', 2)

    def DO_ST_1125(self):
        # Auf Eingabe der Bestaetigung warten
        self.newstate = 1125

        if self.F_button == self.BU_PREV:
            # zum vorherigen Menue zurueck, an der richtigen Stelle rauskommen!
            self.newstate = 1110 
            self.F_update_display = True
            return

        elif self.F_button == self.BU_NEXT:
            # Bestaetigung erteilt, tatsaechliche Schritte einleiten
            if self.list_index==1 or self.list_index == 2:
                # speichern oder speichern und Verlassen
                self.newstate = 1130
                return   
            elif self.list_index == 3:
                # nur Verlassen, laden der alten Einstellungen erfolgt im INIT
                self.newstate = 100 
                self.logger.info('wifi wieder eingeschaltet!')

    def DO_ST_1130(self):
        # Beide Varianten mit Speichern abhandeln, Speicherergebnis ins Display zaubern, 
        if self.list_index==1:
            # Speichern und Verlassen
            self.newstate = 100

        elif self.list_index == 2:
            # nur speichern, zurueck zum Hauptmenue, an den Anfang
            self.newstate = 700
            self.list_index = 1
                          

        self.LCD.clear_data()

        try:
            self.save_to_file()
            self.LCD.write_lines(self.msg_dict["1130"][self.lg], 0,3)
        except:
            self.logger.error(f'{self.state}: Speihern nicht erfolgreich')
            self.LCD.write_single_line(self.msg_dict["1131"][self.lg], 0,3)
        time.sleep(1.0)

        self.F_update_display = True  


    def DO_ST_1190(self):
        # Hilfedatei laden, Position initialisieren
        self.newstate = 1195
        self._load_helptext(1100)

    def DO_ST_1195(self):
        # Hilfetext anzeigen
        self._run_helptext(1110)   

    def DO_ST_1200(self):
        # Sperrzustand. Hier kommt man rein, wenn die Tagesabspielzeit abgelaufen ist, 
        # oder es noch zu frueh oder zu spaet ist. 
        self.newstate = 1250


        self.time_manager.check_status()
        self.time_manager.stop()

        # Funktion wie bei Pause:
        # Musikwiedergabe stoppen
        self.save_current_position()
        self._CheckConnection()
        self.cl.pause(1)
        

        self.LCD.clear_data()
        self.LCD.clear()

        self.LCD.write_lines(self.msg_dict[self.time_manager.status][self.lg], 0, 2)

        # Liste aller zulaesigen Ansagen

        self.play_sound_msg(self.time_manager.status)

    def DO_ST_1250(self):
        # Display ggf. aktulisieren (z.B. Zeit bis zum Start runterzaehlen
        # Auf die Tasten unf RFID reagieren, ggf. ins Editiermenue gehen
        self.newstate = 1250

        # Zeitenverwaltung, ggf. Musikwiedergabe sperren
        self.time_manager.check_status()
        if self.time_manager.status == self.time_manager.status_ok:
            self.play_sound_msg(self.time_manager.status)
            self.newstate = self.ST_PAUSE
            return

        elif self.time_manager.status == self.time_manager.status_morning_limit:
            # aktuelln countdown (Sekunden bis Erreichen des morning_limit) ins Display schreiben
            # derzeit automatisch die Position der Abspielzeitanzeige
            self.LCD.write_time(self.time_manager.countdown)

        elif self.time_manager.status == self.time_manager.status_evening_limit:
            # aktuelln countdown (Sekunden seit erreichen des evening_limit) ins Display schreiben
            # derzeit automatisch die Position der Abspielzeitanzeige
            self.LCD.write_time(self.time_manager.countdown)


        if self.F_button == self.BU_VOLUME_ROTATION:
            # Volume nach Anzahl der Schritte anpassen.
            print(self.N_button)
            # bei schneller Knopfdrehung deutlich mehr reagieren
            if abs(self.N_button) >= 3:
                self.adjust_volume(self.N_button * self.vol_step_Quick)
            else:
                self.adjust_volume(self.N_button * self.vol_step)
        
        # auf jede Art von Input reagieren:
        if (self.F_RFID != self.NO_RFID) or (self.F_button != self.BU_NONE):
            if self.F_RFID in self.MasterCardID:
                # Editiermenue ist erlaubt und wird ausgefuehrt
                self.newstate = self.ST_EDIT_START
            else:
                # sonst immer hier verbleiben, ja nach aktuellem Sperrgrund eine 
                # passende, aber zufaellige Ansage durchfuehren
                self.play_sound_msg(self.time_manager.status)

    def DO_ST_1300(self):
        # So wie Zusatand 200, aber für Internetradio
        # laden und komplett im Display anzeigen, immer weiter nach 250!
        self.newstate = 1350

        # Internetradio: keine Verbindung zum Internet testen
        if self._check_internet() == False:
            # abbrechen, Melsdung abspielen
            self._CheckConnection()
            self.cl.stop()
            self.play_sound_msg('nointernet')
            self.newstate = self.ST_WAIT

            return    

        # wird nicht bereits abgespielt, in MPD laden, sofern eine Verbindung besteht
        if self._CheckConnection():
            # Neue Playliste laden
            self.info['playlist'] = self.playlist_request

            self.LCD.clear()
            self.LCD.clear_data()

            self.cl.clear()            # aktuelle abspielliste loeschen, sonst wird die Playliste nur dazugeladen!
            # Hier kommen wir auch direkt nach Neustart rein. Ein Fehlerhaftes Laden ist moeglich, wenn die letzte
            # gespeicherte Playliste nicht mehr vorhanden ist. --> Abfangen so wie im Zustand 170!!
            try: 
                self.cl.load(self.info['playlist'])
            except:
                self.logger.error("Fehler 1300: self.cl.load(self.info['playlist']) ")
                self.newstate = 400
                return
            self.cl.play()

            # Kompletten Playlistennamen darstellen
            self._writeMessage(self.playlist_request)

        else: 
            # nochmal im naechsten zyklus versuchen
            self.newstate = 1300
            self.logger.info('loop state 1300 wegen connection MPD')
            return        

    def DO_ST_1350(self):
        # So wie 250, aber für Internetradio
        # kontinuierliches Abspielen der Musik, auf Tasten reagieren, Display aktualisieren,...
        # ohne Ereignis bleiben wir hier
        self.newstate = 1350

        # Zeitenverwaltung, ggf. Musikwiedergabe sperren
        self.time_manager.count()
        self.time_manager.check_status()
        if self.time_manager.status != self.time_manager.status_ok:
            self.newstate = self.ST_BLOCKED
            return

        if self.F_RFID != self.NO_RFID:
            self.newstate = self.ST_LOADLIST
            return

        # auf Abbruch der Internetverbindung testen
        if self.elapsed_time(self.TIMER_WLAN_CHECK): 
            if self._check_internet():
                self.start_timer(self.TIMER_WLAN_CHECK)
            else:
                self._CheckConnection()
                self.cl.stop()
                self.play_sound_msg('nointernet')
                self.newstate = self.ST_WAIT
                return

        # jetzt erst die Tastereingabe verarbeiten
        if self.F_button != self.BU_NONE or (self.elapsed_time(self.TIMER_DISPLAY) and not self._validMessage()):
            self._CheckConnection()
            self.update_MPD_info()
            self.F_update_display = True

            # Verbindung zu MPD herstellen, falls noetig. 

            if self.F_button == self.BU_PREV:
                # Kommando an MPD schicken, dass Titel zurueck (falls moeglich)
                # todo: Fehler beim Abspielen eines Internetradios:
                # - warum auf dem einen ok, dem anseren aber nicht?
                # - wie abfangen?
                # --> eigene Fehlermeldung akustisch, dass Intenetradio nicht verfuegbar oder falsch
                if self._check_prev():
                    try:
                        # immer zurueck zum ersten Radio. Wenn eines nicht tut, dann kann man nicht darueber zurueck.
                        # Wenn es nicht tut, wird es beim vorwaerts gehen automatisch uebersprungen.  
                        self.cl.play(1)  
                    except:
                        self.logger.error("Fehler 1350: self.cl.previous() ")

            elif self.F_button == self.BU_NEXT:
                # Titel vor, (falls moeglich)
                if self._check_next():
                    try:
                        self.cl.next()
                    except:
                        self.logger.error("Fehler 1350: self.cl.next() ")

            elif self.F_button == self.BU_PAUSE:
                # Pause ausloesen und in den Zustand ST_PAUSE wechseln
                self.cl.pause(1)
                self.LCD.quick_update_state('pause')
                self.newstate = self.ST_PAUSE
                
            elif self.F_button == self.BU_VOLUME_ROTATION:
                # Volume nach Anzahl der Schritte anpassen.
                # bei schneller Konpfdrehung deutlich mehr reagieren
                if abs(self.N_button) >= 3:
                    self.adjust_volume(self.N_button * self.vol_step_Quick)
                else:
                    self.adjust_volume(self.N_button * self.vol_step)

            self.update_MPD_info()

        # Displayupdate bei Anforderung
        if self.F_update_display or ((self.cur_disp_page == self.DISP_MESSAGE) and not self._validMessage()):
            self._writeRadio()
            self.start_timer(self.TIMER_DISPLAY)
            self.F_update_display = False        

    def DO_ST_1400(self):
        # ERROR_DISPLAY
        # Anzeige einer Fehlermeldung
        self.newstate = 1450

        self.cl.stop()
        # Anzeige der Fehlerursache

        if self.exception:
            #helptext = traceback.print_exc()
            ex = self.exception
            helptext = ''.join(traceback.format_exception(etype=type(ex), value=ex, tb=ex.__traceback__))

        else:
            helptext = 'ST_1400: No Exception recieved.'

        self.__load_errortext(helptext)

    def DO_ST_1450(self):
        # ERROR_DISPLAY
        # Anzeige einer Fehlermeldung, auf Quittieren warten
        self.newstate = 1450
        # auf Tasteneingabe warten, danach nach WAIT
        self._run_helptext(400)
        
    def DO_ST_1500(self):
        # Eingangszustand Playlistenauswahl
        self.newstate = 1505
        # Liste aller Playlisten aktualisieren, Titel Nummerieren
        # aehlich State 700
        update_all_playlists(self.cfg_gl['foname_music'],self.cfg_gl['foname_playlists']) 
        # Liste aller abspielbaren Playlisten
        self.all_pl = read_playlists(self.cfg_gl['foname_playlists'])

        # indexierung der Playlistenelemente, hier zweckentfremdet
        self._index_key = 0

        # Display loeschen und neu fuellen
        self.LCD.clear()
        self.LCD.write_lines(self.msg_dict["1500"][self.lg], 0, 2)
        self.LCD.write_single_line(self.generate_footer(prev='EXIT',), 2)

    def DO_ST_1505(self): 
        # Anzeige des Eingangszustads, bis irgendwas gedrueckt wird
        self.newstate = 1505

        # RFID sticht alle, sofort zum Verarbeiten der Karte. Todo: klappt das auch mit der Mastercard?
        if self.F_RFID != self.NO_RFID:
            self.newstate = self.ST_LOADLIST
            return

        if self.F_button != self.BU_NONE:
            if self.F_button == self.BU_PREV:
                # wieder abbbrechen, Zielzustand je nach aktuellem MPD-Zustand, wird im 1599 verarbeitet.
                self.newstate = 1599

            elif self.F_button == self.BU_NEXT:
                # zur Hilfe gehen
                self.newstate = 1590
            else:
                # zur Playlitenauswahl gehen, das erste Element anzeigen ueber alle 3 Zeilen
                self.newstate = 1550


    def DO_ST_1550(self):
        # die aktuell darzustellende Playliste ueber 3 Zeilen anzeigen
        self.newstate = 1555
        self.LCD.clear()
        # Anzeigetext:  "xxx/yyy: Voller Name der Playliste"
        self.LCD.write_lines(f'{self._index_key+1}/{len(self.all_pl)}: {self.all_pl[self._index_key]}', 0, 3)
        
    def DO_ST_1555(self):
        # Auf alle Eingabe reagieren, waehrend eine Playlite angezeigt wird.

        if self.F_RFID != self.NO_RFID:
            self.newstate = self.ST_LOADLIST
            return

        if self.F_button != self.BU_NONE:

            if self.F_button == self.BU_PREV:
                # verlassen, Zielsustand wird anhand von MPD entschieden
                self.newstate = 1599
 
            elif self.F_button == self.BU_NEXT:
                # zur Hilfe
                self.newstate = 1590

            elif self.F_button == self.BU_PAUSE:
                # Den aktuellen Titel waehlen, dann nach 200?
                self.playlist_request = self.all_pl[self._index_key]
                self.newstate = 200

            elif self.F_button == self.BU_PAUSE_ROTATION:
                return

            elif self.F_button == self.BU_VOLUME_ROTATION:
                # Eine andere Playliste der Liste anzeigen, Reaktion entsprechen der registrierten 
                # Raster, aber index auf die Liste "self.all_pl" beschraenken
                self._index_key = (self._index_key+self.N_button) % len(self.all_pl)
                self.newstate = 1550

    def DO_ST_1590(self):
        # Hilfedatei laden, Position initialisieren
        self.newstate = 1595
        self._load_helptext(1590)

    def DO_ST_1595(self):
        # Hilfetext anzeigen
        self._run_helptext(1550)   


    def DO_ST_1599(self):
        # Zustand des Verlassens, hier wird entschieden, wo wir hingehen
        
        self.update_MPD_info()
        self.LCD.clear()
        if self.info['state'] == 'play':
            # todo: Abspieldisplay mit Play ???
            self.newstate = 250
            self._writePlay()
        elif self.info['state'] == 'pause':
            # todo: Abspieldisplay mit Pause
            self.newstate = 350
            self._writePlay()
        else:
            self.newstate = 400

    # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # ++++++++++++++++    Ende      Zustandsfunktionen +++++++++++++++++++++++++++
    # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

    def ubi(self):
        # Methode, die jeden Zustand immer ausgeführt wird.
        if self.state != self.newstate:
            self.logger.info(str(self.state)+"--> "+str(self.newstate))
        else:
            self.logger.debug(str(self.state)+"--> "+str(self.newstate))


        self.laststate = self.state


        if (self.F_shutdown == True) and (self.F_shutdownCalled==False):
            self.state = self.ST_SHUTDOWN
            self.logger.info(f'{self.state}: Shutdown gerufen!')
        else:
            if self.newstate == self.NO_NEWSTATE:
                raise ValueError(f'state {self.state}: no newstate defined!')
            else:
                self.state = self.newstate
        self.newstate = self.NO_NEWSTATE

        # RFID zyklisch auslesen
        if self.elapsed_time(self.TIMER_RFID):
            self.start_timer(self.TIMER_RFID)
            # Rueckgabe entweder False oder eben irgendeine RFID (str, 12 Stellen)
            try:
                self.F_RFID = self.reader.readID()
            except:
                # sporadisch tritt ein Fehler beim Auslesen auf, generell abfangen
                self.logger.error(f'state {self.state}: Fehler RFID auslesen!')
                self.F_RFID = self.NO_RFID

            # LED (und Backlight) bei ausgelesener RFID setzen
            if self.F_RFID != self.NO_RFID:
                GPIO.output(self.PINS[PIN_LED], GPIO.HIGH)
                self.start_timer(self.TIMER_LED)
                if self.BacklightMode == self.BL_OnBUTTON:
                    self.LCD.setBacklight(GPIO.HIGH,0)
                    self.start_timer(self.TIMER_BACKLIGHT)


        # jetzt wird der Code des aktuellen Zustandes abgearbeitet. 
        try:
            self.state_dict[self.state]()

        except Exception as ex:
            self.state = 1400
            self.exception = ex
            self.state_dict[self.state]()
            # self.state_dict[1400]()
            self.logger.debug(str(self.state)+"--> "+str('1400'))

        # Nacharbeitung: 
        # - Buttons zuruecksetzen
        # - LED_action ausschalten
        # - Display-Backlight verwalten
        # - Display-Laufschrift weiterlaufen lassen
        self.F_button = self.BU_NONE
        self.N_button = 0

        if self.elapsed_time(self.TIMER_LED):
            GPIO.output(self.PINS[PIN_LED], GPIO.LOW)

        # optionale HIntergrundbeleuchtung des Displays ggf. abschalten
        if self.BacklightMode == self.BL_OnBUTTON:
            if self.elapsed_time(self.TIMER_BACKLIGHT):
                self.LCD.setBacklight(GPIO.LOW,0)

        # allgemeines Displayupdate von Laufschrift, Zustandsunabhaengig
        if self.elapsed_time(self.TIMER_DISPLAY):
            self.start_timer(self.TIMER_DISPLAY)
            self.LCD.update_ls() 

        # WLAN abschalten im Musikbetrieb. Achtung: nach derzeitigem Stand nicht vernuenftig umkehrbar,
        # nur mit Neustart wieder OK. 
        if (self.state < 700):
            if (self.wlansetting == 'off') and (self.wlan==True):
                if self.elapsed_time(self.TIMER_WLAN):
                    block_wifi()
                    self.logger.info('WLAN abgeschaltet!')    
                    self.wlan=False    


        # zum Abschluss die Zykluszeit schlafen
        time.sleep(self.cycletime)

        



                                







                