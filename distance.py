#!/usr/bin/env python3

from time import sleep, perf_counter_ns
from gpiozero import DistanceSensor
from reporting import DeviceReporter

REPORT_FREQUENCY = 1000

# Set up ultrasonic sensor
## https://www.woolseyworkshop.com/2020/05/01/interfacing-ultrasonic-distance-sensors-with-a-raspberry-pi/
dist_sensor = DistanceSensor(echo=23, trigger=24, max_distance=4)

# Set up reporting to Losant
reporter = DeviceReporter()

last_report = None
distance_mm_raw = None
distance_buffer = []
while True:
    start_iteration = perf_counter_ns() / 1000000
    
    # Get reading and save to buffer
    distance_mm_raw = dist_sensor.distance * 1000
    distance_buffer.append(distance_mm_raw)

    # If time to report, take average of buffer and send
    duration = start_iteration - last_report if last_report != None else REPORT_FREQUENCY
    if(duration >= REPORT_FREQUENCY):
        last_report = start_iteration
        s = sum(distance_buffer)
        l = len(distance_buffer)
        m = s / l
        print(f"Reporting state: {m}mm from {l} readings over {duration/1000} seconds" )
        reporter.report("distance",sum(distance_buffer) / len(distance_buffer))
        distance_buffer.clear()

    # Verify loop iteration did not take more than 25 ms to ensure we get the full benefit of the sensor's 40 readings a secopnd
    duration = (perf_counter_ns() / 1000000) - start_iteration
    if duration > 25 :
        print(f"WARNING Iteration took more than 25ms")


    sleep(0.025) # 40 times a second