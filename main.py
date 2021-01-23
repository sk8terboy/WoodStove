# -*- coding: utf-8 -*-
import time
from temperature import Temperature
from motor import Motor
from servomotor import ServoMotor
from pid import PID
from agenda import Agenda
from enum import Enum
from web_server import WebServer
import paho.mqtt.client as mqtt

class State(Enum):
    FIRE_OUT = 0 # Feu eteint
    TEMPERATURE_RISE = 1 # Montée en température
    TEMPERATURE_FALL = 2 # Baisse de température
    FIRE_STABLE = 3 # Feu stable
    FIRE_OVERHEAT = 4 # Feu trop fort
    
class Mode(Enum):
    AUTOMATIC = 0 # Target set by room temperetaure and airflow set by PID
    SEMI_AUTOMATIC = 1 # Airflow set by PID
    MANUAL = 2 # Airflow set by user

##K = 0.01
##T = 10
##L = 1
##PID_TEMP_P_GAIN = 1.2 * T / L
##PID_TEMP_I_GAIN= 0.6 * T / (L * L) 
##PID_TEMP_D_GAIN = 0.6 * T
##PID_TEMP_MIN_I_ERROR = -2000
##PID_TEMP_MAX_I_ERROR = 2000

# PID constants
K = 1.0
DEFAULT_PID_TEMP_P_GAIN = 2.5
DEFAULT_PID_TEMP_I_GAIN= 0.5
DEFAULT_PID_TEMP_D_GAIN = 2800.0
PID_TEMP_MIN_I_ERROR = 0.0
PID_TEMP_MAX_I_ERROR = 100.0
DEFAULT_TEMP_TARGET = 130.0

MAX_TEMPERATURE_NUMBER = 200

# Room temperature management constants
MQTT_BROKER_ADDR = "192.168.1.100"
MIN_ROOM_TEMP = 16.0
MAX_ROOM_TEMP = 20.0
MIN_TARGET_TEMP = 130.0
MAX_TARGET_TEMP = 180.0
TARGET_SLOPE = (MIN_TARGET_TEMP - MAX_TARGET_TEMP) / (MAX_ROOM_TEMP - MIN_ROOM_TEMP)
TARGET_INTERCEPT = MAX_TARGET_TEMP - MIN_ROOM_TEMP * TARGET_SLOPE

temperatures = []
airflows = []
newValue = False
targetSet = False

tempTarget = DEFAULT_TEMP_TARGET
tempTargetDiff = 0.0
currentTemp = 0.0
currentMode = Mode.AUTOMATIC
currentState = State.FIRE_OUT
currentRoomTemp = 0.0
    
# def motorTest():
    # print("rotate(True, 1, 3):  {:.3f}".format(motor.getAngle()))
    # motor.rotate(True, 1, 3)
    # time.sleep(1)
    # print("rotate(False, 2, 3): {:.3f}".format(motor.getAngle()))
    # motor.rotate(False, 2, 3)
    # time.sleep(1)
    # print("rotateAngle(-90): {:.3f}".format(motor.getAngle()))
    # motor.rotateAngle(-90, 3)
    # time.sleep(1)
    # print("setAirFlow(50): {:.3f}".format(motor.getAngle()))
    # motor.setAirFlow(50)
    # time.sleep(1)
    # print("setAirFlow(75): {:.3f}".format(motor.getAngle()))
    # motor.setAirFlow(75)
    # time.sleep(1)
    # print("setAirFlow(75) 2: {:.3f}".format(motor.getAngle()))
    # motor.setAirFlow(75)
    # time.sleep(1)
    # print("setAirFlow(100): {:.3f}".format(motor.getAngle()))
    # motor.setAirFlow(100)
    # time.sleep(1)
    # print("rotateAngle(-90): {:.3f}".format(motor.getAngle()))
    # motor.rotateAngle(-90, 3)
    # print("Angle at the end: {:.3f}".format(motor.getAngle()))
    
# def motorTest2():
    # print("setAirFlow(50): {:.3f}".format(motor.getAngle()))
    # motor.setAirFlow(50)
    # time.sleep(1)
    # print("setAirFlow(75): {:.3f}".format(motor.getAngle()))
    # motor.setAirFlow(75)
    # time.sleep(1)
    # print("setAirFlow(0): {:.3f}".format(motor.getAngle()))
    # motor.setAirFlow(0)
    # time.sleep(1)
    # print("setAirFlow(100): {:.3f}".format(motor.getAngle()))
    # motor.setAirFlow(100)
    # print("Angle at the end: {:.3f}".format(motor.getAngle()))
    
# def motorTest3():
    # for i in range(25, -1, -1):
        # print("setAirFlow({}): {:.3f}".format((i * 4) - 1, motor.getAngle()))
        # motor.setAirFlow((i * 4) - 1)
        # print("setAirFlow({}): {:.3f}".format(i * 4, motor.getAngle()))
        # motor.setAirFlow(i * 4)
    # for i in range(0, 26, 1):
        # print("setAirFlow({}): {:.3f}".format((i * 4) - 1, motor.getAngle()))
        # motor.setAirFlow((i * 4) - 1)
        # print("setAirFlow({}): {:.3f}".format(i * 4, motor.getAngle()))
        # motor.setAirFlow(i * 4)
    # print("setAirFlow({}): {:.3f}".format(i * 4, motor.getAngle()))
    
# def motorTest4(minPercent):
    # print("setAirFlow(0): {:.3f}".format(motor.getAngle()))
    # for i in range(100, minPercent+1, -1):
        # motor.setAirFlow(i)
        # print("setAirFlow({}): {:.3f}".format(i, motor.getAngle()))
        # # motor.setAirFlow(i - 2)
        # # print("setAirFlow({}): {:.3f}".format(i - 2, motor.getAngle()))
        # time.sleep(0.1)
    # for i in range(minPercent, 101, 1):
        # # motor.setAirFlow(i + 2)
        # # print("setAirFlow({}): {:.3f}".format(i + 2, motor.getAngle()))
        # motor.setAirFlow(i)
        # print("setAirFlow({}): {:.3f}".format(i, motor.getAngle()))
        # time.sleep(0.1)
    
# def motorTest5():
    # print("rotateAngle(45): {:.3f}".format(motor.getAngle()))
    # motor.rotateAngle(45, 1);
    # time.sleep(5);
    # print("rotateAngle(-45): {:.3f}".format(motor.getAngle()))
    # motor.rotateAngle(-45, 1);
    # print("Angle end: {:.3f}".format(motor.getAngle()))
    
def on_message(client, userdata, message):
    global currentRoomTemp
    currentRoomTemp = float(message.payload.decode("utf-8"))
    
def callback(message):
    global newValue, targetSet, temperatures, currentRoomTemp, airflows, tempTarget, currentMode, currentState, currentAirFlow, pid, motor
    msg = message.split(',')
    if msg[0] == 'Get':
        if msg[1] == 'Temperature':
            if newValue:
                newValue = False
                str = ''
                length = len(temperatures)
                for i in range(0, length):
                    str = str + ',{:.2f},{:.2f},{:d}'.format(temperatures[i][0], temperatures[i][1], airflows[i])
                return 'Temperature' + str
            else:
                return None
        elif msg[1] == 'RoomTemperature':
            return 'RoomTemperature,{:.1f}'.format(currentRoomTemp)
        elif msg[1] == 'Target':
            return 'Target,{:d}'.format(int(tempTarget))
        elif msg[1] == 'Airflow':
            return 'Airflow,{:d}'.format(motor.getAirFlow())
        elif msg[1] == 'State':
            return 'State,{:s}'.format(currentState.name)
        elif msg[1] == 'Mode':
            return 'Mode,{:d}'.format(currentMode.value)
        elif msg[1] == 'Kp':
            return 'Kp,{:.4f}'.format(pid.p_gain)
        elif msg[1] == 'Ki':
            return 'Ki,{:.4f}'.format(pid.i_gain)
        elif msg[1] == 'Kd':
            return 'Kd,{:.4f}'.format(pid.d_gain)
        elif msg[1] == 'PidOut':
            return 'PidOut,{:.2f}'.format(pid.last_output)
    elif msg[0] == 'Set':
        if msg[1] == 'Airflow':
            motor.setAirFlow(int(msg[2]))
            print('Airflow set to {:d}'.format(motor.getAirFlow()))
        elif msg[1] == 'Target':
            tempTarget = int(msg[2])
            # global currentTemp
            # currentTemp = int(msg[2])
            targetSet = True
            print('Target set to ' + msg[2])
        elif msg[1] == 'Mode':
            currentMode = Mode(int(msg[2]))
            print('Mode set to ' + currentMode.name)
        elif msg[1] == 'Kp':
            pid.p_gain = float(msg[2])
            print('Kp set to ' + msg[2])
        elif msg[1] == 'Ki':
            pid.i_gain = float(msg[2])
            pid.setIntegralMinMax(PID_TEMP_MIN_I_ERROR / pid.i_gain, PID_TEMP_MAX_I_ERROR / pid.i_gain);
            print('Ki set to ' + msg[2])
        elif msg[1] == 'Kd':
            pid.d_gain = float(msg[2])
            print('Kd set to ' + msg[2])
    else:
        return None
   
def testStateTemperatureRise():
    global temperatures
    return len(temperatures) >= 4 and (temperatures[-4][1] - temperatures[-1][1]) < 0.0
    
def testStateTemperatureFall():
    global temperatures, tempTargetDiff
    return tempTargetDiff >= 5.0 and len(temperatures) >= 4 and (temperatures[-4][1] - temperatures[-1][1]) > 0.0
    
def testStateFireOut():
    global currentTemp
    return currentTemp < 30.0
    
def testStateFireOverheat():
    global tempTargetDiff
    return tempTargetDiff < -5.0
    
def testStateFireStable():
    global tempTargetDiff
    return tempTargetDiff < 5.0
   
if __name__ == "__main__":    
    server = WebServer(callback)
    agenda = Agenda()
    temp = Temperature()
    motor = ServoMotor()
    client = mqtt.Client("mqtt_client")
    
    # time.sleep(5)
    # motorTest4(15)
    
    client.connect(MQTT_BROKER_ADDR)
    print("Connection to broker at " + MQTT_BROKER_ADDR)
    client.on_message = on_message
    client.loop_start()
    client.subscribe("shellies/shellyht-ADC6D7/sensor/temperature")
    print("Subscription to room temperature topic")
    
    pid = PID(DEFAULT_PID_TEMP_P_GAIN, 
            DEFAULT_PID_TEMP_I_GAIN,
            DEFAULT_PID_TEMP_D_GAIN,
            PID_TEMP_MIN_I_ERROR / DEFAULT_PID_TEMP_I_GAIN, 
            PID_TEMP_MAX_I_ERROR / DEFAULT_PID_TEMP_I_GAIN, 
            time.time())
    pid.reinit(tempTarget, temp.getFilteredTemperature(), time.time())
    targetSet = True
      
    while 1:
        try:
            currentTemp = temp.getFilteredTemperature()
            
            if currentMode == Mode.AUTOMATIC and not currentRoomTemp == 0.0:
                tempTarget = TARGET_SLOPE * currentRoomTemp + TARGET_INTERCEPT
                if tempTarget < MIN_TARGET_TEMP:
                    tempTarget = MIN_TARGET_TEMP
                elif tempTarget > MAX_TARGET_TEMP:
                    tempTarget = MAX_TARGET_TEMP
                print('Target set to ' + str(tempTarget) + ' in automatic mode')
            
            tempTargetDiff = tempTarget - currentTemp
            
            temperatures.append([time.time(), currentTemp])
            airflows.append(motor.getAirFlow())
            if len(temperatures) > MAX_TEMPERATURE_NUMBER:
                temperatures = temperatures[-MAX_TEMPERATURE_NUMBER:]
                airflows = airflows[-MAX_TEMPERATURE_NUMBER:]
            newValue = True
            
            print('Temperature: {0:.2f}, Room temperature: {1:.1f}, State: {2}, Current Air Flow: {3}'.format(currentTemp, currentRoomTemp, currentState, motor.getAirFlow()))
        
            # if not currentMode == Mode.MANUAL:
                # if tempTargetDiff < 10:
                    # pidOut = pid.compute(currentTemp, tempTarget, time.time())
                    # print('\tPID - out: {0}'.format(pidOut))
                    # if not targetSet:
                        # # motor.setAirFlow(int(K * pidOut))
                        # print('\tAir Flow set: {0}, Angle: {1}'.format(motor.getAirFlow(), motor.getAngle()))
                    # else:
                        # targetSet = False
                # else:
                    # pid.reinit(tempTarget, currentTemp, time.time())
                    # motor.setAirFlow(100)
                    
            if not currentMode == Mode.MANUAL:
                if currentState == State.FIRE_OUT:
                    if not testStateFireOut():
                        if testStateTemperatureRise():
                            currentState = State.TEMPERATURE_RISE
                        elif testStateFireStable():
                            pid.reinit(tempTarget, currentTemp, time.time())
                            targetSet = False
                            currentState = State.FIRE_STABLE
                            print("\tStart servoing")
                        elif testStateFireOverheat():
                            pid.reinit(tempTarget, currentTemp, time.time())
                            targetSet = False
                            currentState = State.FIRE_OVERHEAT
                            print("\tStart servoing")
                elif currentState == State.TEMPERATURE_RISE:
                    if testStateFireOverheat():
                        pid.reinit(tempTarget, currentTemp, time.time())
                        targetSet = False
                        currentState = State.FIRE_OVERHEAT
                        print("\tStart servoing")
                    elif testStateFireStable():
                        pid.reinit(tempTarget, currentTemp, time.time())
                        targetSet = False
                        currentState = State.FIRE_STABLE
                        print("\tStart servoing")
                    elif testStateTemperatureFall():
                        currentState = State.TEMPERATURE_FALL
                        agenda.send_alert()
                    motor.setAirFlow(100)
                elif currentState == State.TEMPERATURE_FALL:
                    motor.setAirFlow(100)
                    if testStateFireStable():
                        pid.reinit(tempTarget, currentTemp, time.time())
                        targetSet = False
                        currentState = State.FIRE_STABLE
                        print("\tStart servoing")
                    elif testStateTemperatureRise():
                        currentState = State.TEMPERATURE_RISE
                        agenda.delete_alert()
                    elif testStateFireOut():
                        currentState = State.FIRE_OUT
                        agenda.delete_alert()
                elif currentState == State.FIRE_STABLE or \
                     currentState == State.FIRE_OVERHEAT:
                    pidOut = pid.compute(currentTemp, tempTarget, time.time())
                    if not targetSet:
                        motor.setAirFlow(int(K * pidOut))
                        print('\tAir flow set: {0}, Angle: {1}'.format(motor.getAirFlow(), motor.getAngle()))
                    else:
                        targetSet = False
                    if testStateTemperatureFall():
                        currentState = State.TEMPERATURE_FALL
                        agenda.send_alert()
                        print("\tStop servoing")
            
            time.sleep(10)
        except Exception as e:
            print("\nServer stopped: ", e)
            break