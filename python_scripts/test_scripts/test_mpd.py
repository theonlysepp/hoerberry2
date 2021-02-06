# Testskript, um Muskwiedergabe mit dem MPDClient zu starten  
# und die Lautstaerkeregelung zu testen


from mpd import MPDClient
import time
from subprocess import call

client = MPDClient()               # create client object
client.timeout = 10                # network timeout in seconds (floats allowed), default: None
client.idletimeout = None          # timeout for fetching the result of the idle command is handled seperately, default: None


client.connect("localhost", 6600)  # connect to localhost:6600 muss ggf vor jedem 
                                   # Befehl an den client wiederholt werden. MPD bricht die
                                   # Verbindung selbsstandig ab nach einiger Zeit. 

try:                                   
    client.load("Felix_Abenteuerliche-Briefe")
    client.listplaylist("Felix_Abenteuerliche-Briefe")    # Liste aller Titel in der Playliste
    client.play(1)
    
    
    print("Musikwiedergabe laeuft")
    
    time.sleep(5)
    call('amixer set Master 50%',shell=True)
    print("80%")
    
    time.sleep(5)
    call('amixer set Master 30%',shell=True)
    print("30%")
    
    time.sleep(5)
    call('amixer set Master 80%',shell=True)
    print("80%")
    
    client.pause()
    
finally:
    client.pause()



