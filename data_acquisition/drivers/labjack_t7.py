'''
DRIVER INSTALLATION: https://support.labjack.com/docs/python-for-ljm-windows-mac-linux
EXAMPLE CODE: https://github.com/labjack/labjack-ljm-python/blob/master/Examples/More/Utilities/thermocouple_example_ain_ef.py

Created by Daniel C. Sweeney 
Date: July 12, 2024
'''

import sys
from enum import Enum

from labjack import ljm

class TC_TYPE(Enum):
    TYPE_E = 20
    TYPE_J = 21
    TYPE_K = 22
    TYPE_R = 23
    TYPE_T = 24
    TYPE_S = 25
    TYPE_N = 27
    TYPE_B = 28
    TYPE_C = 30 

class TC_UNIT(Enum):
    K = 0
    C = 1
    F = 2


class LABJACK_T7:
    metadata = dict()
    handle = None
    cjcAddress = 60052 # Cold junction compensation register
    cjcSlope = 1.0  # Cold junction compensation slope
    cjcOffset = 0.0 # Cold junction compensation offset
    channels: list = []

    def __init__(self, serial_num="ANY", ip_addr="ANY", port="ANY"):
        self.handle = ljm.openS(serial_num, ip_addr, port) 
        self.initialize()
        self.get_metadata()

    def get_metadata(self):
        return self.metadata
    
    def initialize(self):
        info = ljm.getHandleInfo(self.handle)
        self.metadata['T7 Device'] = 'Labjack T7'
        self.metadata['T7 Device Type'] = info[0]
        self.metadata['T7 Connection Type'] = info[1]
        self.metadata['T7 Serial Number'] = info[2]
        self.metadata['T7 IP Address'] = ljm.numberToIP(info[3])
        self.metadata['T7 Port'] = info[4]
        self.metadata['T7 Max Bytes/MB'] = info[5]
        print("Opened a LabJack with Device type: %i, Connection type: %i,\n"
            "Serial number: %i, IP address: %s, Port: %i,\nMax bytes per MB: %i" %
            (info[0], info[1], info[2], ljm.numberToIP(info[3]), info[4], info[5]))
    
    def addSingleEndedTC(self, channelName, tcIndex=TC_TYPE.TYPE_K, tempUnitIndex=TC_UNIT.C):        
        resIndexRegister = f"{channelName}_RESOLUTION_INDEX"
        ljm.eWriteName(self.handle, resIndexRegister, 0)

        negChannelValue = ljm.constants.GND
        negChannelRegister = f"{channelName}_NEGATIVE_CH"
        ljm.eWriteName(self.handle, negChannelRegister, negChannelValue)

        # Configure all of the necessary thermocouple AIN_EF registers
        aNames = []
        aValues = []
        # For setting up the AIN#_EF_INDEX (thermocouple type)
        indexRegister = "%s_EF_INDEX" % channelName
        aNames.append(indexRegister)
        aValues.append(tcIndex.value)
        # For setting up the AIN#_EF_CONFIG_A (temperature units)
        configA = "%s_EF_CONFIG_A" % channelName
        aNames.append(configA)
        aValues.append(tempUnitIndex.value)
        # For setting up the AIN#_EF_CONFIG_B (CJC address)
        configB = "%s_EF_CONFIG_B" % channelName
        aNames.append(configB)
        aValues.append(self.cjcAddress)
        # For setting up the AIN#_EF_CONFIG_D (CJC slope)
        configD = "%s_EF_CONFIG_D" % channelName
        aNames.append(configD)
        aValues.append(self.cjcSlope)
        # For setting up the AIN#_EF_CONFIG_E (CJC offset)
        configE = "%s_EF_CONFIG_E" % channelName
        aNames.append(configE)
        aValues.append(self.cjcOffset)
        # Write all of the AIN_EF settings
        ljm.eWriteNames(self.handle, len(aNames), aNames, aValues)

        # Store configuration in metadata
        self.metadata[f'T7 Ch {channelName} Device'] = 'TC'
        self.metadata[f'T7 Ch {channelName} Cold Junction Compensation'] = True
        self.metadata[f'T7 Ch {channelName} TC Type'] = tcIndex.name
        self.metadata[f'T7 Ch {channelName} TC Unit'] = tempUnitIndex.name
        self.metadata[f'T7 Ch {channelName} CJC Slope'] = self.cjcSlope
        self.metadata[f'T7 Ch {channelName} CJC Offset'] = self.cjcOffset
        # self.channels.append(channelName)
        self.channels.append(f'{channelName}_EF_READ_A')

    def addFlow4_20mA(self, channelName:str, conversion_factor=1.0, units=None, shunt_resistance=240):
        channel_number = int(channelName.split('AIN')[-1])
        assert channel_number % 2 == 0, '[X] ERROR: Differential channel must be the positive channel index + 1 (e.g. AIN2(+) and AIN3(-))'

        resIndexRegister = f"{channelName}_RESOLUTION_INDEX"
        ljm.eWriteName(self.handle, resIndexRegister, 0)

        negChannelName = f'AIN{channel_number+1}'
        negChannelRegister = f"{channelName}_NEGATIVE_CH"
        ljm.eWriteName(self.handle, negChannelRegister, channel_number+1)
        
        self.metadata[f'T7 Ch {channelName} Device'] = 'Flow Meter'
        self.metadata[f'T7 Ch {channelName} Flow Meter Units'] = units
        self.metadata[f'T7 Ch {channelName} Configuration'] = 'Differential'
        self.metadata[f'T7 Ch {channelName} Negative Reference'] = f'AIN{negChannelName}'
        self.metadata[f'T7 Ch {channelName} Flow Meter Conversion Factor'] = conversion_factor
        self.metadata[f'T7 Ch {channelName} Shunt Resistance'] = shunt_resistance
        self.channels.append(channelName)

    def measure(self):
        data_packet = dict()
        vals = ljm.eReadNames(self.handle, len(self.channels), self.channels)
        for channelName, val in zip(self.channels, vals):
            key = f'T7 Ch {channelName} Device'
            if key in self.metadata:
                if self.metadata[key] == 'Flow Meter':
                    resistor = self.metadata[f'T7 Ch {channelName} Shunt Resistance']
                    conversion_factor = self.metadata[f'T7 Ch {channelName} Flow Meter Conversion Factor']
                    # print(val)
                    dat = (0.39)/(1.338-0.46)*(val - 0.46)
                    # dat = (val * conversion_factor)/(0.016 * resistor) - conversion_factor/4
                    # dat = (val/resistor - 0.004)*conversion_factor/0.016

            else:
                dat = val
                
            data_packet[f'{channelName}'] = dat
        return data_packet
    
    def shutdown(self):
        ljm.close(self.handle)

if __name__ == '__main__':
    import time
    daq = LABJACK_T7()
    for ch in range(14):
        daq.addSingleEndedTC(f'AIN{ch}')

    print(daq.get_metadata())
    for i in range(5):
        print(daq.measure())
        time.sleep(1.0)
    daq.shutdown()