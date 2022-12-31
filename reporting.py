from losantmqtt import Device

DEVICE_ID = "63b027a5f4f9ead7f48d3bec"
DEVICE_KEY = "d3ecf944-b63a-4af4-b88d-26673acb8b40"
DEVICE_SECRET = "2a8059ed6ddbec337e9913de0959b707b654ecb9c5a63e4e8933a4be85abe9ef"

class DeviceReporter:

    def __init__(self):
        self.device = Device(DEVICE_ID, DEVICE_KEY, DEVICE_SECRET)
        self.device.connect(blocking=False)

    def report(self,key,val):
        self.device.send_state({key: val})

    def keepalive(self):
        self.device.loop()