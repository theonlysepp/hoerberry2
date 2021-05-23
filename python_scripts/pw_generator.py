
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

    line_list = ascii_str.splitlines()
    # Zeile mit dem Passwort in Klartext rausschmeissen
    for i in line_list:
        if i[0:4] == '#psk':
            del(line_list[i])

    # in die Datei schreiben
    with open('/etc/wpa_supplicant/wpa_supplicant.conf','a') as fobj:
             fobj.writelines(line_list)


if __name__ == "__main__":

    add_wlan('testname', 'testpassword')