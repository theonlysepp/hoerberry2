# coding: utf-8
# beliebigen Laufschrifttest fuer eine Displayfeld erzeugen
# bei zu kurzen strings wird fuer das Feld passend aufgefuellt, so dass (ohne 
# Laufschrift) der komplette Platz als String zurueckgegeben wird. 

MODE_FIX   = 0       # garnicht weiterschalten
MODE_FLOAT = 1       # einzeln weiterschalten
MODE_PAGE  = 2       # komplette Laenge weiterschalten


class Laufschrift():
    def __init__(self, laenge, os_front=4, os_back=4, format='left'):
        
        # universelle EIgenschaften des Laufschriftfensters
        self.laenge = laenge
        self.os_front = os_front
        self.os_back = os_back
        if format in ('left', 'right', 'center'):
            self.format = format
        else:
            self.format = 'left'    

        # Eigenschaften des aktuell darzustellenden Strings oder der aktuellen Darstellung
        self.base_string = ''
        self.total_string=''
        self.ii = 0
        self.ii_max = 0
        self.mode = MODE_FLOAT
        self.page_counter = 0
        self.page_char = 0                  # Anzahl darzustellende Zeichen auf der Seite
        self.floating = False               # flag, ob ueberhaupt Laufschrift angezeigt werden muss
        
    def setbase(self, new_string):
        # komplett neuen String in der Laufschrift darstellen, wenn er neu ist
        # dazu alles zuruecksetzen
        if new_string != self.base_string:
            self.base_string = new_string
            
            if len(self.base_string) > 2*self.laenge:
                self.mode = MODE_FLOAT
                self.total_string = self.os_front*' ' + self.base_string + self.os_back* ' '
                self.ii = 0
                self.ii_max = len(self.base_string)+ self.os_front + self.os_back - self.laenge + 1

            elif len(self.base_string) > self.laenge:   
                self.mode = MODE_PAGE
                self.total_string = self.base_string + (2*self.laenge-len(self.base_string))*' '
                self.ii = 0
                self.page_counter = 0
                self.ii_max = len(self.base_string)+ self.os_front + self.os_back - self.laenge + 1

            else:
                self.mode = MODE_FIX
                # total-string auf self.laenge ausdehnen, mit passenden FOrmatierung!!
                self.total_string = self.auto_complete(self.base_string)
                self.ii = 0
                         
    def auto_complete(self,s):
        # den base_string gemaess der Formatieranweisung auf die volle Laenge 
        # gemaess self.laenge auffuellen
        l = len(s)
        
        if self.format == 'left':
            return s + (self.laenge-l)*' '
        elif self.format == 'right':
            return (self.laenge-l)*' ' + s
        elif self.format =='center':
            # recht und links jeweils ein Leerzeichen auffuellen. Am Ende im Zweifel
            # links ein leerzeichen wegnehmen, wenn noetig
            while len(s) < self.laenge:
                s = ' ' + s + ' '     
            if len(s)==self.laenge:
                return s
            else:
                return s[1:-1]        


                
    def step(self, step=1):
        # Laufschrifttext gewuenschte Schritte weiterwandern lassen
        if self.mode == MODE_FLOAT:
            # Sonderfall, wenn ii_max erreicht wird: Sprung nach -1, von dort wieder 
            # in die normale Reihe einreihen.
            if self.ii==-1:
                self.ii = 0
            elif self.ii == self.ii_max-1:
                self.ii = -1
            else:
                self.ii = (self.ii+1) % self.ii_max

        elif self.mode == MODE_PAGE:
            self.page_counter += 6

            if self.page_counter >= self.page_char:
                if self.ii == self.laenge:
                    self.ii = 0
                else:
                    self.ii = self.laenge
                # Anzahl der tatsaechlichen Zeichen berechnen (alles ohne Leerzeichen )
                self.page_char = self.laenge - self.total_string[self.ii:self.ii+self.laenge].count(' ')
                self.page_counter = 0

        elif self.mode == MODE_FIX:
            pass
        else:
            print("unbekannter Modus")
        
    def get(self):
        # aktuellen Teil der Laufschrift ausgeben lassen
        
        if self.mode == MODE_FLOAT:
            # Beim Laufschriftsprung zurueck zum Anfang einmal komplett leer anzeigen
            if self.ii == -1:
                return self.laenge*' '
            else: 
                return self.total_string[self.ii:self.ii+self.laenge]

        elif self.mode == MODE_PAGE:

            return self.total_string[self.ii:self.ii+self.laenge]



        else:
            return self.total_string   
        
    def stepget(self,step=1):
        # Schrittweite und Ausgabe in einer Methode
        self.step(step)
        return self.get()




#test
if __name__ == "__main__":

    import time
                    
    print('Test Laufschrift start.')                
    ls = Laufschrift(16,os_front=1, os_back=1, format='left')
    
    # statischer Test
    ls.setbase('Test')
    print(ls.get())
    ls.step()
    print(ls.get())
    time.sleep(3)

    sleep_time = 0.3

    # Test der eigentlichen Laufschrift
    ls.setbase('kurz')
    i=0
    while i < 20:
        print(ls.get())
        ls.step()
        i += 1
        time.sleep(sleep_time)
    #           0123456789ABCDEF0123456789ABCDEF
    ls.setbase('lang genug fuer den page Mode')
    i=0
    while i < 20:
        print(ls.get())
        ls.step()
        i += 1
        time.sleep(sleep_time)
    #           0123456789ABCDEF0123456789ABCDEF
    ls.setbase('zu lang fuer den page Mode, weil es extra lang ist')
    i=0
    while i < 20:
        print(ls.get())
        ls.step()
        i += 1
        time.sleep(sleep_time)
    
    
    
    
         
                            