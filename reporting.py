from losantmqtt import Device
from losantrest import Client
from time import sleep



class Reporter:

    def __init__(self,device_id, device_key, device_secret):
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

    def __init__(self,device_id, device_key, device_secret):
        self.device = Device(device_id, device_key, device_secret)
    
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

    def __init__(self,device_id, device_key, device_secret):
        self.device_id = device_id
        client = Client()
        creds = {
            'deviceId': device_id,
            'key': device_key,
            'secret': device_secret
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
