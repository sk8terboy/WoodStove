from math import log
import Adafruit_ADS1x15

class Temperature:
    __U = 3.3                     # Supply voltage
    __R = 9680.0 # 10000.0        # Resistance of the divider bridge
    __BETA = 3250 # 3586.0        # Rhermistor constant
    __R0 = 10000.0                # Thermistor reference resistance
    __T0 = 298.16                 # Reference temperature
    __ALPHA = 0.15                # Filter coefficient
    __old_filtered_value = 0.0
    __adc = Adafruit_ADS1x15.ADS1115()
    
    def __init__(self):
        self.__adc.start_adc(0, gain=1)
        
    def getFilteredTemperature(self):
        value = self.__getTemperature(self.__adc.get_last_result())
        
        if self.__old_filtered_value == 0.0:
            new_filtered_value = value
        else:
            new_filtered_value = self.__ALPHA * value + (1 - self.__ALPHA) * self.__old_filtered_value
            
        self.__old_filtered_value = new_filtered_value
        
        return new_filtered_value
    
    def __getTemperature(self, val):
        ut = val * 4.096 / 32768.0  # Measured voltage
        rt = (self.__U * self.__R - ut * self.__R) / ut
        
        print("\t\tUt: {:.5f}".format(ut))
        # print("\t\tRt: {:.5f}".format(rt))
        # print("\t\tRt/R25: {:.5f}".format(rt/self.__R0))
        # print("\t\tT: {:.5f}".format(1/((log(rt/self.__R0)/self.__BETA)+(1/self.__T0))-273.16))
        
        return 1.0/((log(rt/self.__R0)/self.__BETA)+(1/self.__T0))-273.16
    
    def stopAcquisition(self):
        self.__adc.stop_adc()