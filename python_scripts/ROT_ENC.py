#!/usr/local/bin/python
# coding: UTF-8
'''
ROT_ENC Class for rotary encoder

provide callback-functions for signals from rotary encoders, with additional
bounce-suppression.

not tested.
supposed: clockwise = +1
          anticlockwise = -1

'''


import RPi.GPIO as GPIO
from time import sleep
import logging

class ROT_ENC:

    CLOCKWISE = +1
    ANTICLOCKWISE = -1

    def __init__(self, clockPin, dataPin, rotaryCallback, second_callback=None, debounce=15, debounce_extra=1, sleeptime=0.001):
        self.logger = logging.getLogger(__name__)  

        #persist values
        self.clockPin = clockPin
        self.dataPin = dataPin
        self.rotaryCallback = rotaryCallback          # callable, expects two arguments: rotaryCallback(pin, direction)
        self.second_callback = second_callback        # callable, expects two arguments: second_callback(pin, direction)
        self.DEBOUNCE = debounce                      # self.DEBOUNCE in ms
        self.debounce_extra = debounce_extra          # number of cycles with stable signal
        self.sleeptime = sleeptime                    # sleep time cycle, sec

        #setup pins
        GPIO.setup(clockPin, GPIO.IN)
        GPIO.setup(dataPin, GPIO.IN)

    def start(self):
        GPIO.add_event_detect(self.clockPin, GPIO.FALLING, bouncetime=self.DEBOUNCE)
        GPIO.add_event_callback(self.clockPin,self._clockCallback)


    def stop(self):
        GPIO.remove_event_detect(self.clockPin)
        GPIO.remove_event_detect(self.dataPin)
    
    def _clockCallback(self, pin):
        """
        if GPIO.input(self.clockPin) == 0:
            self.rotaryCallback(GPIO.input(self.dataPin))
        """
        # erste Drehrichtungsbestimmung anhand der Momentaufnahme bei der Flanke
        guess = GPIO.input(self.dataPin)  
        ii = 0

        while ii < self.debounce_extra:
            sleep(self.sleeptime)
            ii += 1

            # signal was not stable
            if (GPIO.input(self.clockPin) == GPIO.HIGH) or (guess != GPIO.input(self.dataPin)):
                self.logger.debug('debounce extra cycle {}'.format(ii))
                return
        

        # signals were stable all the time 
        # determin correct orientation:
        if guess == GPIO.HIGH:
            self.rotaryCallback(self.clockPin, self.CLOCKWISE)  
            if callable(self.second_callback): 
                self.second_callback(self.clockPin, self.CLOCKWISE) 
        else:
            self.rotaryCallback(self.clockPin, self.ANTICLOCKWISE)  
            if callable(self.second_callback): 
                self.second_callback(self.clockPin, self.ANTICLOCKWISE) 



#test
if __name__ == "__main__":

    print('Program start.')

    # Pinbelegung laden
    from pinbelegung_testscripts import *
    # Pinbelegung gemaess Gesamtplan
    GPIO.setmode(GPIO.BOARD)

    # LED 
    GPIO.setup(LED_ACTION_PIN, GPIO.OUT)

    def drehVolume(pin, direction):
        print("DrehVolume {}".format(direction))
        
    def drehPause(pin, direction):
        print("DrehPause {}".format(direction))

    def LEDblink(pin, direction=0):
        # LED fuer x ms
        GPIO.output(LED_ACTION_PIN, GPIO.HIGH)
        sleep(0.005)
        GPIO.output(LED_ACTION_PIN, GPIO.LOW)

    volume = ROT_ENC(VolumePIN_CLK, VolumePIN_DT, drehVolume, 
                           second_callback=LEDblink, debounce=15, debounce_extra=1, sleeptime=0.001)
    pause = ROT_ENC(PausePIN_CLK, PausePIN_DT, drehPause, 
                           second_callback=LEDblink, debounce=15, debounce_extra=1, sleeptime=0.001)

    print('Launch switch monitor class.')

    volume.start()
    pause.start()
    print('Start program loop...')
    try:
        while True:
            sleep(10)
            print('Ten seconds...')
    finally:
        print('Stopping GPIO monitoring...')
        volume.stop()
        pause.stop()
        GPIO.cleanup()
        print('Program ended.')

