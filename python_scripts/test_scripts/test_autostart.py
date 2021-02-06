#!/usr/bin/env python
# -*- coding: utf8 -*-

# Test der autostartfunktion mit service
# Alle Ausgaben koennen mit "systemctl status autostart.service" abgerufen werden.

import time
print('autostart gerufen')

from subprocess import call
call('sudo speaker-test -c 2 -t wav -l 2', shell=True )

