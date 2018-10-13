import argparse
import sys
import time
import datetime
import os
from datetime import timedelta
from random import Random
from configparser import ConfigParser

import unide
import requests
from requests_futures.sessions import FuturesSession
from unide.measurement import Measurement, MeasurementPayload, Device
from unide.util import dumps

r = Random()

parser = argparse.ArgumentParser()
parser.add_argument("-c")
args = parser.parse_args()
config = ConfigParser()
config.add_section("ConnectionSettings")
config.add_section("DeviceSettings")
if(args.c):
    print("Reading from " + args.c)
    config.read(args.c)
else:
    config.read("options.ini")

monitoringEndpoint = os.getenv("MONITORING_ENDPOINT", config.get("ConnectionSettings", "MonitoringEndpoint", fallback="https://example.com/"))
print("Endpoint: " + monitoringEndpoint)
authHeader = os.getenv("AUTH_HEADER", config.get("ConnectionSettings", "AuthHeader", fallback=None))
print("Auth Header: " + str(authHeader))
maxRetries = os.getenv("MAX_RETRIES", config.getint("ConnectionSettings", "MaxRetries", fallback=10))
print("Max Retries: " + str(maxRetries))
timeout = os.getenv("TIMEOUT", config.getint("ConnectionSettings", "Timeout", fallback=30))
print("Timeout: " + str(timeout))
msBetweenMeasurements = os.getenv("MS_BETWEEN_MEASUREMENTS", config.getint("DeviceSettings", "MSBetweenMeasurements", fallback=50))
print("Milliseconds between measurements: " + str(msBetweenMeasurements))
measurementsPerMessage = os.getenv("MEASUREMENTS_PER_MESSAGE", config.getint("DeviceSettings", "MeasurementsPerMessage", fallback=100))
print("Measurements per message: " + str(measurementsPerMessage))
deviceId = os.getenv("DEVICE_ID", config.get("DeviceSettings", "DeviceID", fallback=("drone" + str(r.randint(1,1000)))))
print("Device ID: " + deviceId)

device = Device(deviceId)

currentSeries = ["temperature", "humidity", "pressure"]

m = Measurement(unide.process.local_now(), dimensions=currentSeries)
a = requests.adapters.HTTPAdapter(max_retries=maxRetries)
session = FuturesSession()
session.mount('http://', a)
session.headers = {
    "Content-Type": "application/json",
    "Authorization": authHeader
}


def bg_cb(sess, resp):
    # parse the json storing the result on the response object
    resp.data = resp.json()
    print(resp)


while True:
    lastMeasurement = datetime.datetime.utcnow()
    temperature = r.randint(10, 40)
    humidity = r.randint(10, 90)
    pressure = r.randint(900, 1100)
    m.add_sample(unide.process.local_now(), temperature=temperature, humidity=humidity, pressure=pressure)

    if len(m.series.offsets) >= measurementsPerMessage:
        print("Sending message")
        payload = MeasurementPayload(device=device, measurements=[m])
        content = dumps(payload)
        result = session.post(monitoringEndpoint, data=content, background_callback=bg_cb, timeout=timeout)

        # Reset measurement object
        m = Measurement(unide.process.local_now(), dimensions=currentSeries)

    timeToSleep = ((lastMeasurement + timedelta(milliseconds=msBetweenMeasurements)) - datetime.datetime.utcnow()).total_seconds()
    if timeToSleep < 0:
        timeToSleep = 0
    time.sleep(timeToSleep)
