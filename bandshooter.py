from gpiozero import Servo
import time

GPIO_PIN = 25

class BandShooter:

    def __init__(self):
        self.servo = Servo(GPIO_PIN,initial_value=None )

    def shoot(self):
        self.servo.max()
        time.sleep(0.45)
        self.servo.detach()

    
