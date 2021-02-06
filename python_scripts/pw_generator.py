
import subprocess


def find_all(a_str, sub):
    start = 0
    while True:
        start = a_str.find(sub, start)
        if start == -1: return
        yield start
        start += len(sub) # use start += 1 to find overlapping matches


def add_wlan(wlanname, password):
    p = subprocess.Popen(["wpa_passphrase", wlanname, password], stdout=subprocess.PIPE)
    return_stuff = p.communicate()
  
    ascii_str = return_stuff[0].decode('ascii')

    # Position aller Zeilenumbrueche erstellen
    newlines = list(find_all(ascii_str, '\n\t'))
    # Zeile mit dem Passwort in Klartext rausschmeissen
    string_to_file = ascii_str[0:newlines[1]] + ascii_str[newlines[2]::]
    print(string_to_file)

    # in die Datei schreiben
    with open('/etc/wpa_supplicant/wpa_supplicant.conf','a') as fobj:
             fobj.write(string_to_file)


if __name__ == "__main__":

    add_wlan('testname', 'testpassword')