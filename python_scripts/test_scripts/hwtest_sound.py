# Testskript, um Muskwiedergabe mit dem MPDClient zu starten  
# und die Lautstaerkeregelung zu testen


from mpd import MPDClient
import time
import subprocess 

client = MPDClient()               # create client object
client.timeout = 20                # network timeout in seconds (floats allowed), default: None
client.idletimeout = None          # timeout for fetching the result of the idle command is handled seperately, default: None
test_time = 3                      # Zeit fuer jeden Schritt

client.connect("localhost", 6600)  # connect to localhost:6600 muss ggf vor jedem 
                                   # Befehl an den client wiederholt werden. MPD bricht die
                                   # Verbindung selbsstandig ab nach einiger Zeit. 
                                   
def set_vol(volume):
    subprocess.Popen(["sudo", "amixer", "set", "Master", '{:02d}%'.format(volume)], stdout=subprocess.PIPE)




try:                                   
    client.load("Felix_Abenteuerliche-Briefe")
    client.listplaylist("Felix_Abenteuerliche-Briefe")    # Liste aller Titel in der Playliste
    client.play(1)
    
    
    print("Musikwiedergabe laeuft")
    
    time.sleep(test_time)
    set_vol(80)
    print("80%")
    
    time.sleep(test_time)
    set_vol(30)
    print("30%")
    
    time.sleep(test_time)
    set_vol(80)
    print("80%")
    
    time.sleep(test_time)

    client.pause()
    client.stop()
    
finally:

    client.stop()



