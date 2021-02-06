#!/usr/bin/env python

# Pinbelegung und Pfad zu den Modulen
from pinbelegung_testscripts import *

# dogmlcd von hier: https://github.com/Gadgetoid/DogLCD, danach aber modifiziert. 
import doglcd, datetime, time, threading

import RPi.GPIO as GPIO
# __init__(self, lcdSI, lcdCLK, lcdRS, lcdCSB, pin_reset, pin_backlight):





# mit backlight
# alte Belegung mit GPIO.setmode(GPIO-BMC)
#lcd = doglcd.DogLCD(10,11,25,8,-1,DISPLAY_BL_PIN)
# neue Belegung einheitlich mit GPIO.setmode(GPIO.BOARD)
lcd = doglcd.DogLCD(DISPLAY_SI,DISPLAY_CLK,DISPLAY_RS,DISPLAY_CSB,-1,DISPLAY_BL_PIN)

lcd.begin(doglcd.DOG_LCD_M163, 0x28)

# backlight setzen. 


lcd.clear()
lcd.home()
lcd.write(chr(0xFF) + 'OMG! Such time' + chr(0))
lcd.setCursor(0,1)
lcd.write(chr(1) + chr(4) + ' Very Wow! ' + chr(3) + chr(2) + chr(5))


class StoppableThread(threading.Thread):
	def __init__(self):
		threading.Thread.__init__(self)
		self.stop_event = threading.Event()
		self.daemon = True

	def start(self):
		if not self.isAlive():
			self.stop_event.clear()
			threading.Thread.start(self)

	
	def stop(self):
		if self.isAlive():
			self.stop_event.set()
			self.join()


class AsyncWorker(StoppableThread):
	def __init__(self, fn):
		StoppableThread.__init__(self)
		self.fn = fn
		self.iterations = 0

	def run(self):
		while not self.stop_event.is_set():
			if not self.fn(self.iterations):
				break
			self.iterations += 1

def dosweep(i):
	hue = i%360
	time.sleep(0.05)
	return True

blfade = AsyncWorker(dosweep)

try:
	blfade.start()
except KeyboardInterrupt:
	blfade.stop()
	raise

pirate = [
	[0x00,0x1f,0x0b,0x03,0x00,0x04,0x11,0x1f],
	[0x00,0x1f,0x16,0x06,0x00,0x08,0x03,0x1e],
	[0x00,0x1f,0x0b,0x03,0x00,0x04,0x11,0x1f],
	[0x00,0x1f,0x05,0x01,0x00,0x02,0x08,0x07]
]

heart = [
	[0x00,0x0a,0x1f,0x1f,0x1f,0x0e,0x04,0x00],
	[0x00,0x00,0x0a,0x0e,0x0e,0x04,0x00,0x00],
	[0x00,0x00,0x00,0x0e,0x04,0x00,0x00,0x00],
	[0x00,0x00,0x0a,0x0e,0x0e,0x04,0x00,0x00]
	]

raa = [
	[0x1f,0x1d,0x19,0x13,0x17,0x1d,0x19,0x1f],
	[0x1f,0x17,0x1d,0x19,0x13,0x17,0x1d,0x1f],
	[0x1f,0x13,0x17,0x1d,0x19,0x13,0x17,0x1f],
	[0x1f,0x19,0x13,0x17,0x1d,0x19,0x13,0x1f]
	]

arr = [
	[31,14,4,0,0,0,0,0],
	[0,31,14,4,0,0,0,0],
	[0,0,31,14,4,0,0,0],
	[0,0,0,31,14,4,0,0],
	[0,0,0,0,31,14,4,0],
	[0,0,0,0,0,31,14,4],
	[4,0,0,0,0,0,31,14],
	[14,4,0,0,0,0,0,31]
]

char = [
	[12,11,9,9,25,25,3,3],
	[0,15,9,9,9,25,27,3],
	[3,13,9,9,9,27,27,0],
	[0,15,9,9,9,25,27,3]
]

pacman = [
	[0x0e,0x1f,0x1d,0x1f,0x18,0x1f,0x1f,0x0e],
	[0x0e,0x1d,0x1e,0x1c,0x18,0x1c,0x1e,0x0f]
]




def getAnimFrame(char,fps):
	return char[ int(round(time.time()*fps) % len(char)) ]

ii=1
bl=GPIO.LOW

# while 1:
# 	lcd.createChar(0,getAnimFrame(char,4))
# 	lcd.createChar(1,getAnimFrame(arr,16))
# 	lcd.createChar(2,getAnimFrame(raa,8))
# 	lcd.createChar(3,getAnimFrame(pirate,2))
# 	lcd.createChar(4,getAnimFrame(heart,4))
# 	lcd.createChar(5,getAnimFrame(pacman,3))
# 	lcd.setCursor(0,2)
# 	t = datetime.datetime.now().strftime("%H:%M:%S.%f")
# 	lcd.write(t)

# 	# backlight zyklisch ein und ausschalten
# 	ii += 1
# 	if ii==100:
# 		ii=0
# 		if bl==GPIO.LOW:
# 			bl=GPIO.HIGH
# 		else:
# 			bl=GPIO.LOW

# 		lcd.setBacklight(bl,0)
	
symbols = [ [0,10,10,10,10,10,10,0],    
            [0,0,15,15,15,15,15,0],   
            [0,8,12,14,15,14,12,8],
			[0,4,0x0a,0x12,0x14,0x12,0x14,0] ]  # Darstellung des "ß"

lcd.clear()


lcd.write(chr(0)+'  '+chr(1)+'   '+chr(2)+'   '+chr(3))

lcd.createChar(0,symbols[0])
time.sleep(2)
lcd.createChar(1,symbols[1])
time.sleep(2)
lcd.createChar(2,symbols[2])
time.sleep(2)
lcd.createChar(3,symbols[3])

time.sleep(2)
lcd.setBacklight(0,1)
lcd.write(chr(0))
lcd.write("test")
lcd.createChar(0,symbols[0])
