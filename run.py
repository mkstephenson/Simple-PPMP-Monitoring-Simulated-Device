import time
import datetime
import os
from datetime import timedelta
from random import Random

import unide
import requests
from requests_futures.sessions import FuturesSession
from unide.measurement import *

monitoringEndpoint = os.getenv("MONITORING_ENDPOINT", "http://localhost:5000")
print("Monitoring endpoint is " + monitoringEndpoint)
authHeader = os.getenv("AUTH_HEADER", "Bearer iksldufgvuzdioasfvg")
print("Auth header is " + authHeader)
msBetweenMeasurements = os.getenv("MS_BETWEEN_MEASUREMENTS", 250)
print("MS between measurements is " + msBetweenMeasurements)
measurementsPerMessage = os.getenv("MEASUREMENTS_PER_MESSAGE", 50)
print("Measurements per message is " + measurementsPerMessage)
deviceId = os.getenv("DEVICE_ID", "drone1")
print("Device ID is " + deviceId)
maxRetries = os.getenv("MAX_RETRIES", 50)
print("Max retries is " + maxRetries)

device = Device(deviceId)

r = Random()

currentSeries = ["temperature", "humidity", "pressure"]

m = Measurement(unide.process.local_now(), dimensions=currentSeries)
a = requests.adapters.HTTPAdapter(max_retries=maxRetries)
session = FuturesSession()
session.mount('http://', a)
session.headers = {
    "Content-Type": "application/json",
    "Authorization": authHeader
}

print("Starting request loop")

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
        result = session.post(monitoringEndpoint, data=content)

        # Reset measurement object
        m = Measurement(unide.process.local_now(), dimensions=currentSeries)

    time.sleep(((lastMeasurement + timedelta(
        milliseconds=msBetweenMeasurements)) - datetime.datetime.utcnow()).total_seconds())
