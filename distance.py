#!/usr/bin/env python
import threading
from time import sleep, time_ns, perf_counter_ns
from gpiozero import DistanceSensor
from gpiozero.pins.pigpio import PiGPIOFactory
from reporting import RESTReporter
from bandshooter import BandShooter
import numpy as np

REPORT_FREQUENCY = 2000
DISTANCE_SENSOR_DEVICE_ID = "63b027a5f4f9ead7f48d3bec"
SHOOTER_DEVICE_ID = "63b0565c412b132160b22368"

# Set up reporting to Losant
distance_device = RESTReporter(DISTANCE_SENSOR_DEVICE_ID)
shooter_device = RESTReporter(SHOOTER_DEVICE_ID)

# { device: DeviceReporter, states: [] }
distance_reports = [] 


my_factory = PiGPIOFactory()

# Set up ultrasonic sensor
## https://www.woolseyworkshop.com/2020/05/01/interfacing-ultrasonic-distance-sensors-with-a-raspberry-pi/
dist_sensor = DistanceSensor(echo=23, trigger=24, max_distance=4, pin_factory=my_factory)

# Set up rubber band shooter
shooter = BandShooter()

# Mutex locks
lock = threading.Lock() # reporting queue
shooting_cv = threading.Condition()
report_cv = threading.Condition()


###### Kalman matrices

def init_matrices():
    # Current state [ [distance (mm), velocity (mm/ms)] ]
    X = np.array( [[4000],[10]] ) 

    # Current uncertainty
    P = np.array([ [100,0],
                   [0,1000] ])

    return X,P



def sensing():

    global distance_reports

    last_report = None
    distance_mm_raw = None
    distance_reports_buffer = [] 

    X, P = init_matrices()

    # Process noise
    Q = np.array([ [.1,0],
                [0,.1] ])

    # State to measurement matrix
    # Converts state ([distance,velocity]) to measurement form ([distance]) for operations
    H = np.array([ [1,0] ] )

    # Observation uncertainty matrix
    # higher numbers represent more confidence in readings
    R = np.array( [3] )

    idle = True


    # Monitor sensor
    while True:
        start_iteration = perf_counter_ns() / 1000000
        duration = start_iteration - last_report if last_report != None else REPORT_FREQUENCY
        
        # Get raw reading
        distance_mm_raw = int(dist_sensor.distance * 1000)

        # Reset state if wasn't detecting anything and is detecting something now
        if idle and distance_mm_raw < 4000:
            X, P = init_matrices()
            idle = False
        elif not idle and distance_mm_raw >= 4000:
            X, P = init_matrices()
            idle = True

        ## ------------
        ## PREDICT PHASE
        ## ------------

        # State transition matrix
        # How should the next state be predicted based on current state?
        F = np.array([ [1,-1 * duration],
                      [0,1] ])
        X_HAT = F @ X
        P_HAT = F @ P @ F.T


        ## ------------
        ## OBSERVE PHASE
        ## ------------


        # Observation
        Z = distance_mm_raw
        K = P_HAT @ H.T @ np.linalg.inv(H @ P_HAT @ H.T + R)
        X = X_HAT + K @ ( Z - H @ X_HAT )
        P = P_HAT - K @ H @ P_HAT


        ## ------------
        ## VALUE READY
        ## ------------

        distance = X[0][0]
        velocity = X[1][0]

        ## Shoot if distance will be < 500mm in 1000ms
        one_second_F = np.array([ [1,-1 * 1000],
                      [0,1] ])
        one_second_X_HAT = one_second_F @ X
        if one_second_X_HAT[0][0] < 500:
            with shooting_cv:
                shooting_cv.notify_all()


        if not idle or duration >= REPORT_FREQUENCY: 
            # save every measurement during activity
            # save interval measurement during inactivity
            distance_reports_buffer.append({
                "time": time_ns() / 1000000,
                "data":{
                    "distance": distance_mm_raw,
                    "estimatedDistance": distance,
                    "estimatedVelocity": velocity
                }
            })

        if idle and len(distance_reports_buffer) > 0:
            # copy reports to thread protected buffer when idle and there are any
            with report_cv:
                distance_reports = distance_reports_buffer.copy()
                report_cv.notify_all()
            distance_reports_buffer.clear()

       

        # Verify loop iteration did not take more than 50 ms to ensure we get the full benefit of the sensor's 20 readings a secopnd
        duration = (perf_counter_ns() / 1000000) - start_iteration
        if duration > 50 :
            print(f"WARNING Iteration took more than 50ms")
        else:
            extra_time = 50 - duration
            sleep(extra_time / 1000) # 20 times a second

def reporting():

    reports_copy = []
    while True:
     
        # wait for signal on reports. copy and release lock if it has any
        with report_cv:
            report_cv.wait()
            reports_copy = distance_reports.copy()
            distance_reports.clear()

        # process reports
        if len(reports_copy) > 0:
            distance_device.report_states(reports_copy)
        
        sleep(1)


def shooting():
    while True:
        with shooting_cv:
            shooting_cv.wait()
            shooter.shoot()
           
        shooter_device.report_states(
            [{
                "data": {
                    "shoot": True
                },
                "time": time_ns() / 1000000
            }]
        )
        sleep(5)

sensor_thread = threading.Thread(target=sensing, args=())
sensor_thread.start()

reporting_thread = threading.Thread(target=reporting, args=())
reporting_thread.start()

shooting_thread = threading.Thread(target=shooting, args=())
shooting_thread.start()
