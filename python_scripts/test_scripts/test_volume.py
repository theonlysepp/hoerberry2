# -*- coding: utf8 -*-
# Test der Verstärkerlautstaerke
# zufaelliges Abspielen der deutschen Ansagetexte, mit varabler Lautstaerke
# zum Einstelen des Verstaerkers. Die Hoerbuecher und Lieder sind in der Regel etwas lauter.
# testaenerung

from pathlib import Path
import sys
import hjson
from random import shuffle, randint
import subprocess

# alle relevanten Pfade erzeugen
p_test_skripts=Path('.').absolute()
p_python = p_test_skripts.parent
p_github = p_python.parent
p_settings = Path(p_github, 'settings_and_data')

# Pfad fuer den Modulimport von doglcd hinzufuegen
sys.path.append(str(p_python))

# einmalig der allgemeine Ort von basesettings.ini,
path = Path('/home/pi/audio_messages/deutsch')

soundlist = [e for e in path.iterdir() if e.is_file()]



while True: 
    Vol = input('bitte Lautstaerke eingeben: ')
    subprocess.Popen(["sudo", "amixer", "set", "Master", Vol+'%'], stdout=subprocess.PIPE)
    subprocess.call(f'sudo mpg123 {soundlist[randint(0,len(soundlist)-1)].resolve()}', shell=True)