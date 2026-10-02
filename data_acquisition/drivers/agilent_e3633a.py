'''
PYSERIAL INSTALLATION: https://pyserial.readthedocs.io/en/latest/
AGILENT E3633A MANUAL: https://www.keysight.com/us/en/support/E3633A/200w-power-supply-8v-20a-20v-10a.html

Created by Daniel C. Sweeney 
Date: July 12, 2024
'''


import datetime
import os

import serial
import serial.tools.list_ports

class AGILENT_E3633A:
    ser = None
    metadata = dict()

    def __init__(self, baud=9600, timeout=1, adapter_kw='Prolific'):
        port = self.find_device(kw=adapter_kw)
        self.ser = serial.Serial(port, baud, timeout=timeout)
        self.initialize()
        self.get_metadata()

    def find_device(self, kw='Prolific'):
        ports = ports = serial.tools.list_ports.comports()
        for port, desc, hwid in sorted(ports):
                if kw in desc:
                    print(f'Agilent E3633A found on port {port}: {desc} ({hwid})')
                    self.metadata['E3633A Serial Port'] = port
                    self.metadata['E3633A Serial Port Description'] = desc
                    self.metadata['E3633A Serial Port Hwid'] = hwid
                    return port

    def get_metadata(self):
        return self.metadata

    def query(self, command):
        self.write(command)
        ret = self.ser.readline().decode().rstrip()
        return ret
    
    def write(self, command):
        self.ser.write(f'{command}\r\n'.encode())

    def measure(self):
        data_packet = dict()
        data_packet['E3633A Voltage (V)'] = self.query('MEAS:VOLT?')
        data_packet['E3633A Current (A)'] = self.query('MEAS:CURR?')
        data_packet['E3633A voltage_protection_trip'] = self.query('VOLT:PROT:TRIP?')
        data_packet['E3633A current_protection_trip'] = self.query('CURR:PROT:TRIP?')
        data_packet['E3633A output enabled'] = self.query('OUTP?')
        return data_packet

    def enableOutput(self):
        self.write('OUTP ON')
        output = self.query('OUTP?')
            
    def disableOutput(self):
        self.write('OUTP OFF')
        output = self.query('OUTP?')

    def setVoltage(self, voltage:float):
        self.write(f"VOLT {voltage:3f}")

    def setCurrent(self, current:float):
        self.write(f"CURR {current:3f}")

    def initialize(self):
        self.write("SYST:REM")
        self.metadata['E3633A Instrument'] = 'Agilent E3633A'
        self.metadata['E3633A Serial Number'] = self.query('*IDN?')
        self.metadata['E3633A System Version'] = self.query('SYST:VERS?')
        for _ in range(3):
            self.beep()
        pass

    def beep(self):
        self.write('SYST:BEEP:IMM')

    def shutdown(self):
        self.ser.close()


if __name__ == '__main__':
    import time
    import random
    psu = AGILENT_E3633A()
    print(psu.get_metadata())
    for i in range(5):
        psu.disableOutput()
        psu.setVoltage(random.random()*10)
        print(psu.measure())
        psu.enableOutput()
        time.sleep(5.0)
    psu.disableOutput()
    psu.shutdown()