#!/usr/local/bin/python
# coding: UTF-8

# Testskript fuer die Audioausgabe (hifiberry + Boxen)

import time
from subprocess import call

try:
    call('aplay -l',shell=True)
    
    call('amixer set Master 50%',shell=True)
    
    call('speaker-test -c 2 -t wav -l 1',shell=True)
    
    time.sleep(5)
    
    call('amixer set Master 80%',shell=True)
    call('speaker-test -c 2 -t wav -l 1',shell=True)    
finally:
    print('skript beendet')