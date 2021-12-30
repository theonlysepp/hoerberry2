# -*- coding: utf8 -*-

# Klasse zum Verwalten von zeitlichen Begrenzungen:
# Gesamtdauer
# Startzeit
# Endzeit



from datetime import datetime, time
import hjson
import logging
import subprocess

class TimeManager():

    # Konstanten
    status_ok            = 'ok'
    status_daily_limit   = 'dailylimit'
    status_morning_limit = 'morninglimit'
    status_evening_limit = 'eveninglimit'

    def __init__(self, daily_limit, morning_limit, evening_limit, uptimeinit=0):
        # 
        self.logger = logging.getLogger(__name__)  

        # Zeitserver synchronisiert?
        self.sync = False

        self.daily_limit = daily_limit     # Sekunden

        self.now = datetime.now()  


        self.morning_limit = datetime.combine(self.now.date(),time.fromisoformat(morning_limit))   
        self.evening_limit = datetime.combine(self.now.date(),time.fromisoformat(evening_limit))   
        self.midnight = datetime.combine(self.now.date(), time(0))

        self.uptimeinit = uptimeinit
        self.uptime = uptimeinit     # Stoppuhr, die mitlauft, Sekunden
        self.counting = False

        self.laststart = datetime.now()   # letzter Zaehlbeginn, immer aktualisieren, wenn self.counting=True)

        self.status = self.status_ok
        # Multifunktionaler countdown: 
        # - entweder Zeit, bis das Morning_limit erreicht wird
        # - Zeit, bis das daily_limit erreicht wird
        self.countdown = 0

        # Platzhalter fuer das geladenen Verzeichnis { Datum : uptime }   (uptime in minuten)
        self.data = {}


    def check_time_synchonize(self):
        p=subprocess.Popen(["timedatectl", "status"],stdout=subprocess.PIPE)
        status = p.communicate()

        if status[0].find(b'System clock synchronized: yes') != -1:
            # String gefunden, d.h. Zeitsynchronisation ist aktiv
            # --> alle Zeiten synchronisieren
            self.sync = True
            self.now = datetime.now()  


            if self.morning_limit.date() == self.now.date():
                # gelaufene Zeit zuruecksetzen, weil ich nicht weiss, wieviel durch den Zeitsprung der Aktualisierung 
                # aufsummiert wurde
                self.uptime = self.uptimeinit
                if self.counting:
                    self.laststart = datetime.now() 
            else:
                # die gespeicherten Sekunden waren von einem alten Tag -->
                # aufsummierte Zeit zuruecksetzen!
                self.uptime = 0
                if self.counting:
                    self.laststart = datetime.now() 


            # Wiedergabegrenzen an das aktuelle Datum anpassen
            self.morning_limit = datetime.combine(self.now.date(),self.morning_limit.time())   
            self.evening_limit = datetime.combine(self.now.date(),self.evening_limit.time())   
                    

    def count(self):
       # mitzaehlen starten, wenn nicht schon aktiv
        if self.counting == False:
            self.counting = True
            # Startzeitpunkt notieren 
            self.laststart = datetime.now()

    def stop(self):
        # mitzaehlen stoppen
        if self.counting == True:
            self.counting = False
            dt = datetime.now() - self.laststart
            self.uptime += dt.seconds

    def get_uptime(self):
        # zusammengezaehlte zeit bis jetzt
        if self.counting:
            dt = datetime.now() - self.laststart
            return self.uptime + dt.seconds
        else:
            return self.uptime

    def add_uptime(self, seconds):
        # bereits gelaufene Zeit hinzufuegen
        self.uptime += seconds

    def check_status(self):
        self.now = datetime.now()

        if self.sync == False:
            self.check_time_synchonize()

        # auf Mitternachtssprung testen, ggf. Mitternacht resetten
        if self.midnight.date() != self.now.date():
            self.midnight = datetime.combine(self.now.date(), time(0))
            self.uptime = 0
            self.laststart = self.now

        
        if self.get_uptime() >= self.daily_limit and self.sync:
            # Gesamtzeit ueberschritten
            self.countdown = 0
            self.status = self.status_daily_limit

        elif (self.now < self.morning_limit) and self.sync:
            # zu frueh
            # (nur wenn die aktuelle Uhrzeit wirklich synchronisiert ist)
            delta = self.morning_limit-self.now
            self.countdown = delta.seconds
            self.status = self.status_morning_limit

        elif self.now > self.evening_limit and self.sync:
            # zu spaet,
            # Sekunden seit Ueberschreiten anzeigen
            # (nur wenn die aktuelle Uhrzeit wirklich synchronisiert ist)
            delta = self.now-self.evening_limit
            self.countdown = delta.seconds
            self.status = self.status_evening_limit
        else:
            # Stuts OK
            # Verbleibende Sekunden des Tagespensums
            self.countdown = self.daily_limit - self.get_uptime()
            self.status = self.status_ok

    def save(self,fobj):
        # Datum und Zeit in eine Datei schreiben
        self.get_uptime()

        self.data[self._decode(self.now)] = self.uptime

        hjson.dump(self.data,fobj, default=self._decode)

    def load(self,fobj):
        # Datum und Zeit aus einer Datei laden
        self.data = hjson.load(fobj)
        try:
            if self._decode(datetime.now()) in self.data:
                self.uptime += self.data[self._decode(datetime.now())]
        except KeyError:
            self.logger.error('time_manager.load: data nicht gefunden')

    def _decode(self, o):
        # decoder fuer das Speichern mit Json, umwandeln in sowas: 
        # "2016-04-08"
        if isinstance(o, datetime):
            return "{}-{:02d}-{:02d}".format(o.year, o.month, o.day)
        


# Mitternacht: OK
# aktuelle Zeit : OK
# Zeitdifferenz zu Mittenraht: OK
# Zeitpunkt aus String in Zeit? 
