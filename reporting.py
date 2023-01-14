from losantmqtt import Device
from losantrest import Client
from time import sleep

DEVICE_KEY = "d3ecf944-b63a-4af4-b88d-26673acb8b40"
DEVICE_SECRET = "2a8059ed6ddbec337e9913de0959b707b654ecb9c5a63e4e8933a4be85abe9ef"

class Reporter:

    def __init__(self,device_id):
        self.device_id = device_id
        self.device = None

    def connect(self):
        return
    
    def report(self,key,val,time=None):
        return

    def report_states(self,states):
        return
    
    def keepalive(self):
        return
    

class MQTTReporter(Reporter):

    def __init__(self,device_id):
        self.device = Device(device_id, DEVICE_KEY, DEVICE_SECRET)
    
    def connect(self,blocking = False):
        self.device.connect(blocking)

    def report(self,key,val):
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

class RESTReporter(Reporter):

    def __init__(self,device_id):
        self.device_id = device_id
        client = Client()
        creds = {
            'deviceId': device_id,
            'key': DEVICE_KEY,
            'secret': DEVICE_SECRET
        }
        response = client.auth.authenticate_device(credentials=creds)

        client.auth_token = response['token']
        
        self.app_id = response['applicationId']
        self.device = client.device

    def connect(self):
        return
    
    def report(self,key,val,time=None):
        
        state = {'data': {key: val}}
        if time is not None:
            state['time'] = time
        self.device.send_state(deviceId=self.device_id,
            applicationId=self.app_id, deviceState=state)

    def report_states(self,states):
        self.device.send_state(deviceId=self.device_id,
            applicationId=self.app_id, deviceState=states)
        return
    
    def keepalive(self):
        return
