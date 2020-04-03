import time
import pigpio
import subprocess
from subprocess import DEVNULL
from ina219 import INA219
    
class ServoMotor:
    __MIN_ANGLE = 0.0
    __MAX_ANGLE = 201.2
    __LINEAR_COEF = (__MAX_ANGLE - __MIN_ANGLE) / 100.0
    __LINEAR_OFFSET = __MAX_ANGLE - (100.0 * __LINEAR_COEF)
    __MIN_PULSE = 550
    __MAX_PULSE = 2450
    __currentAngle = __MAX_ANGLE - 1.0
    __currentAirFlow = 100
#    __ina = INA219(0.1)
#    __powerSum = 0.0
#    __powerSumCounter = 0
    
    def __init__(self):
        subprocess.Popen(['sudo', 'pigpiod', '-p', '8000'])
        time.sleep(1)
        self.__pwm = pigpio.pi('localhost', '8000')
        tries = 0
        while tries < 3 and not self.__pwm.connected:
            self.__pwm = pigpio.pi('localhost', '8000')
            tries = tries + 1
            time.sleep(1)
        self.__pwm.set_PWM_frequency(18, 50)
        self.rotateAngle(self.__MAX_ANGLE, 15)
#        self.__ina.configure()

    def __getPulseFromAngle(self, angle):
        return float(angle) * (self.__MAX_PULSE - self.__MIN_PULSE) / (self.__MAX_ANGLE - self.__MIN_ANGLE) + self.__MIN_PULSE

    def rotateAngle(self, angle, speed):
        diffAngle = angle - self.__currentAngle
        
        if diffAngle:
            # self.__powerSum = 0.0
            # self.__powerSumCounter = 0
            for i in range(1, 501):
                self.__pwm.set_servo_pulsewidth(18, self.__getPulseFromAngle(self.__currentAngle + i * diffAngle / 500))
                time.sleep(abs(diffAngle) / speed / 500)
                # self.__powerSum += self.__ina.power()
                # self.__powerSumCounter += 1
            self.__currentAngle = angle
            self.__pwm.set_servo_pulsewidth(18, 0)
            # if self.__powerSumCounter == 0:
               # print("Mean power: 0mW")
            # else:        
               # print("Mean power: {:.2f}mW".format(self.__powerSum / self.__powerSumCounter))
        
    def getAngle(self):
        return self.__currentAngle
        
    def setAirFlow(self, percent):
        if percent > 100:
            percent = 100
        if percent < 0:
            percent = 0
        self.__currentAirFlow = percent;
        targetedAngle = self.__LINEAR_COEF * float(percent) + self.__LINEAR_OFFSET
        self.rotateAngle(targetedAngle, 15)
    
    def getAirFlow(self):
        return self.__currentAirFlow
    