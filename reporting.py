from losantmqtt import Device
from time import sleep

DEVICE_KEY = "d3ecf944-b63a-4af4-b88d-26673acb8b40"
DEVICE_SECRET = "2a8059ed6ddbec337e9913de0959b707b654ecb9c5a63e4e8933a4be85abe9ef"

class DeviceReporter:

    def __init__(self,device_id):
        self.device = Device(device_id, DEVICE_KEY, DEVICE_SECRET)
    
    def connect(self,blocking = False):
        self.device.connect(blocking)

    def report(self,key,val):
        self.device.send_state({key: val})

    def connect_and_report(self,key,val):
        self.device.connect(blocking=False)
        sleep(2)
        self.device.send_state({key: val})

    def report(self,key,val,time=None):
        self.device.send_state({key: val},time)

    def report_states(self,states):
        for state in states:
           self.device.send_state(state["data"])

    def close(self):
        self.device.close()

    def keepalive(self):
        self.device.loop()


