
import subprocess


def add_wlan(wlanname, password):
    p = subprocess.Popen(["wpa_passphrase", wlanname, password], stdout=subprocess.PIPE)
    return_stuff = p.communicate()
  
    ascii_str = return_stuff[0].decode('ascii')

    # in Zeilen umwandeln, und Zeile mit dem Passwort in Klartext rausschmeissen
    line_list = [i+'\n' for i in ascii_str.splitlines() if i[0:5] != '\t#psk']

    # in die Datei schreiben
    with open('/etc/wpa_supplicant/wpa_supplicant.conf','a') as fobj:
             fobj.writelines(line_list)


if __name__ == "__main__":

    add_wlan('testname', 'testpassword')