import time

# from agilent_e3633a import AGILENT_E3633A as PSU
from elektroautomatik_9200 import ELEKTROAUTOMATIK_9200 as PSU
# from bkprecision_1747 import BKPRECISION_1747 as PSU
from labjack_t7 import LABJACK_T7
from logger import DATA_LOGGER

if __name__ == '__main__':
    log = DATA_LOGGER()
    # psu = AGILENT_E3633A()
    daq = LABJACK_T7()

    # Add Flow Meter Channel
    daq.addFlow4_20mA('AIN12', 
                      conversion_factor=1,
                      units='L/min', 
                      shunt_resistance=120)

    # Add TC Channels
    for ch in range(0,12):
        daq.addSingleEndedTC(f'AIN{ch}')

    metadata = dict()
    # metadata.update(psu.get_metadata())
    metadata.update(daq.get_metadata())
    log.initialize(metadata)

    # psu.disableOutput()
    # psu.setVoltage(10.)
    # psu.enableOutput()

    # for i in range(10):
    i = 0
    while True:
        meas = dict()
        meas.update(psu.measure())
        meas.update(daq.measure())
        log.write(meas)
        print(f'Measurement {i}: ', meas)
        time.sleep(1.0)

    psu.disableOutput()
    psu.shutdown()
    daq.shutdown()