import time
import math
from random import randrange
import RPi.GPIO as GPIO
from ina219 import INA219

class Motor:
    __MIN_ANGLE = 0.0
    __MAX_ANGLE = 140.0
    __LINEAR_COEF = (__MIN_ANGLE - __MAX_ANGLE) / 100.0
    __LINEAR_OFFSET = __MIN_ANGLE - (100.0 * __LINEAR_COEF)
    __GEAR_RATIO = 2
    __STEP_ANGLE = 360.0 / 64.0 / 64.0 / __GEAR_RATIO * 2
    __STEP_PINS = [26,19,13,6]
    __STEP_SEQ_SIMPLE = [[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]]
    __STEP_SEQ_DEFAULT = [[1,0,0,0],[1,1,0,0],[0,1,0,0],[0,1,1,0],[0,0,1,0],[0,0,1,1],[0,0,0,1],[1,0,0,1]]
    __STEP_SEQ_FULL_TORQUE = [[0,0,1,1],[1,0,0,1],[1,1,0,0],[0,1,1,0]]
    __ENDSTOP_LOW_PIN = 17
    __ENDSTOP_HIGH_PIN = 27
    __currentAngle = __MIN_ANGLE
    __currentAirFlow = 100
    __lastStepTime = 0
##    __ina = INA219(0.1)
##    __powerSum = 0.0
##    __powerSumCounter = 0
    
    def __init__(self, rotationType):
        self.__initPins()
        if rotationType == 1:
            self.__seq = self.__STEP_SEQ_SIMPLE
        elif rotationType == 2:
            self.__seq = self.__STEP_SEQ_DEFAULT
        elif rotationType == 3:
            self.__seq = self.__STEP_SEQ_FULL_TORQUE
##        self.__ina.configure()

    def __initPins(self):
        # Set all pins as output
        GPIO.setmode(GPIO.BCM)
        for pin in self.__STEP_PINS:
          GPIO.setup(pin, GPIO.OUT)
          GPIO.output(pin, False)
        GPIO.setup(self.__ENDSTOP_LOW_PIN, GPIO.IN)
        GPIO.setup(self.__ENDSTOP_HIGH_PIN, GPIO.IN)
          
    def __deinitPins(self):
        GPIO.cleanup()

    def __updateAngle(self, direction, numberSeq):
        if direction:
            self.__currentAngle += numberSeq * self.__STEP_ANGLE * 4
        else:
            self.__currentAngle -= numberSeq * self.__STEP_ANGLE * 4
        
    def __rotateSeq(self, direction, waitTime):
        if direction:
            stepIndex = 0
        else:
            stepIndex = len(self.__seq) - 1
        
        numStep = len(self.__seq)
        stepCounter = 0
        while stepCounter < numStep:
            # TEST
            try:
            # TEST
                now = time.time()
                if (now - self.__lastStepTime) >= waitTime:
                    self.__lastStepTime = now
                    for pin in range(4):
                      xpin = self.__STEP_PINS[pin]
                      if self.__seq[stepIndex][pin] != 0:
                        GPIO.output(xpin, True)
                      else:
                        GPIO.output(xpin, False)
                    if direction:
                        stepIndex += 1
                    else:
                        stepIndex -= 1
                    stepCounter += 1
            # TEST
            except KeyboardInterrupt as e:
                print(e)
                print(now)
                print(self.__lastStepTime)
                print(waitTime)
                print(numStep)
                print(stepCounter)
            # TEST
        time.sleep(waitTime)

    def __getWaitTimeFromSpeed(self, speed):
        if speed == 1:
            waitTime = 0.02
        elif speed == 2:
            waitTime = 0.01
        elif speed == 3:
            waitTime = 0.005
        return waitTime

    def rotate(self, direction, rotationTime, speed):
        waitTime = self.__getWaitTimeFromSpeed(speed)
        self.__initPins()
        startTime = time.time()
        while (time.time() - startTime) < rotationTime:
            self.__updateAngle(direction, 1)
            self.__rotateSeq(direction, waitTime)
        self.__deinitPins()
            
    def rotateAngle(self, angle, speed, toEndStop):
        if angle >= 0.0:
            direction = True
        else:
            direction = False
            
        waitTime = self.__getWaitTimeFromSpeed(speed)
        numberStep = int(math.fabs(float(angle)) / self.__STEP_ANGLE)
        
        self.__updateAngle(direction, numberStep / len(self.__seq))
        
        if toEndStop:
            numberSeq = (numberStep + int(20.0 / self.__STEP_ANGLE)) / len(self.__seq) ## Add 20°
        else:
            numberSeq = numberStep / len(self.__seq)
            
        seqCounter = 0
##        self.__powerSum = 0.0
##        self.__powerSumCounter = 0
        self.__initPins()
        while seqCounter < numberSeq:
            if direction and GPIO.input(self.__ENDSTOP_LOW_PIN):
                print("Endstop low");
                self.__currentAngle = self.__MAX_ANGLE
                break
            if not direction and GPIO.input(self.__ENDSTOP_HIGH_PIN):
                print("Endstop high");
                self.__currentAngle = self.__MIN_ANGLE
                break
            self.__rotateSeq(direction, waitTime)
##            self.__powerSum += self.__ina.power()
##            self.__powerSumCounter += 1
            seqCounter += 1
        self.__deinitPins()
##        if self.__powerSumCounter == 0:
##            print("Mean power: 0mW")
##        else:        
##            print("Mean power: {:.2f}mW".format(self.__powerSum / self.__powerSumCounter))
            
    def getAngle(self):
        return self.__currentAngle
    
    def setAirFlow(self, percent):
        if percent > 100:
            percent = 100
        if percent < 0:
            percent = 0
        self.__currentAirFlow = percent;
        targetedAngle = self.__LINEAR_COEF * float(percent) + self.__LINEAR_OFFSET
        diffAngle = targetedAngle - self.__currentAngle
        if (percent == 0 or percent == 100) and diffAngle != 0:
            toEndStop = True
        else:
            toEndStop = False
        self.rotateAngle(diffAngle, 1, toEndStop)
        
    def getAirFlow(self):
        return self.__currentAirFlow
        