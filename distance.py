#!/usr/bin/env python
import threading
from time import sleep, perf_counter_ns
from gpiozero import DistanceSensor
from gpiozero.pins.pigpio import PiGPIOFactory
from reporting import DeviceReporter
from bandshooter import BandShooter

REPORT_FREQUENCY = 2000
DISTANCE_SENSOR_DEVICE_ID = "63b027a5f4f9ead7f48d3bec"
SHOOTER_DEVICE_ID = "63b0565c412b132160b22368"

# Set up reporting to Losant
distance_device = DeviceReporter(DISTANCE_SENSOR_DEVICE_ID)
distance_device.connect()
shooter_device = DeviceReporter(SHOOTER_DEVICE_ID)
shooter_device.connect()

# { device: DeviceReporter, states: [] }
reports = [] 
my_factory = PiGPIOFactory()

# Set up ultrasonic sensor
## https://www.woolseyworkshop.com/2020/05/01/interfacing-ultrasonic-distance-sensors-with-a-raspberry-pi/
dist_sensor = DistanceSensor(echo=23, trigger=24, max_distance=4, pin_factory=my_factory)

# Set up rubber band shooter
shooter = BandShooter()

# Mutex locks
lock = threading.Lock() # reporting queue
shooting_cv = threading.Condition()


def reporting():

    reports_copy = []
    while True:
        # # Keep network connections alive
        distance_device.keepalive()
        shooter_device.keepalive()
        
        # wait for lock on reports. copy and release lock if it has any
        with lock:
            if len(reports) > 0:
                reports_copy = reports.copy()
                reports.clear()

        # process reports
        while len(reports_copy) > 0:
            r = reports_copy.pop(0)
            r["device"].report_states(r["states"])
        
        sleep(1)

def shooting():
    while True:
        with shooting_cv:
            shooting_cv.wait()
            shooter.shoot()
            print(f"Firing...")
            # wait for lock on reports
            with lock:
                reports.append({
                    "device": shooter_device,
                    "states": [{
                        "data": {
                            "shoot": True
                        },
                        "time": perf_counter_ns() / 1000000
                    }]
                })
        sleep(5)

def sensing():

    last_report = None
    distance_mm_raw = None
    distance_buffer = []

    # Monitor sensor
    while True:
        start_iteration = perf_counter_ns() / 1000000

        # Get reading and save to buffer
        distance_mm_raw = int(dist_sensor.distance * 1000)
        distance_buffer.append(distance_mm_raw)

        # Shoot if really close
        if distance_mm_raw < 1000:
            with shooting_cv:
                shooting_cv.notify_all()


        # If time to report, take average of buffer and send
        duration = start_iteration - last_report if last_report != None else REPORT_FREQUENCY
        if(duration >= REPORT_FREQUENCY):
            last_report = start_iteration
            s = sum(distance_buffer)
            l = len(distance_buffer)
            m = s / l
            print(distance_buffer)
            print("\n")
            print(f"Reporting state: {m}mm from {l} readings over {duration/1000} seconds" )
            #distance_device.report("distance",sum(distance_buffer) / len(distance_buffer))
            distance_buffer.clear()

            # wait for lock on reports
            with lock:
                reports.append({
                    "device": distance_device,
                    "states": [{
                        "data": {
                            "distance": m
                        },
                        "time": start_iteration
                    }]
                })
           

        # Verify loop iteration did not take more than 25 ms to ensure we get the full benefit of the sensor's 40 readings a secopnd
        duration = (perf_counter_ns() / 1000000) - start_iteration
        if duration > 25 :
            print(f"WARNING Iteration took more than 25ms")


        sleep(0.05) # 20 times a second


sensor_thread = threading.Thread(target=sensing, args=())
sensor_thread.start()

reporting_thread = threading.Thread(target=reporting, args=())
reporting_thread.start()

shooting_thread = threading.Thread(target=shooting, args=())
shooting_thread.start()
