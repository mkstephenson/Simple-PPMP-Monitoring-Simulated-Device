import argparse
import sys
import time
import datetime
import os
import json
from datetime import timedelta
from random import Random
from configparser import ConfigParser

import unide
import requests
from requests_futures.sessions import FuturesSession
from unide.measurement import Measurement, MeasurementPayload, Device
from unide.util import dumps

class ValueTemplate():
    def __init__(self, name, min, max):
        self.name = name
        self.min = min
        self.max = max
        

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

# Set monitoring endpoint
monitoringEndpoint = os.getenv("MONITORING_ENDPOINT", config.get("ConnectionSettings", "MonitoringEndpoint", fallback="https://example.com/"))
print("Endpoint: " + monitoringEndpoint)

# Set the HTTP authorization header
authHeader = os.getenv("AUTH_HEADER", config.get("ConnectionSettings", "AuthHeader", fallback=None))
print("Auth Header: " + str(authHeader))

# Set the maximum number of HTTP retries
maxRetries = os.getenv("MAX_RETRIES", config.getint("ConnectionSettings", "MaxRetries", fallback=10))
print("Max Retries: " + str(maxRetries))

# Set the timeout of the connection
timeout = os.getenv("TIMEOUT", config.getint("ConnectionSettings", "Timeout", fallback=30))
print("Timeout: " + str(timeout))

# Set the numnber of milliseconds between simulated measurements
msBetweenMeasurements = os.getenv("MS_BETWEEN_MEASUREMENTS", config.getint("DeviceSettings", "MSBetweenMeasurements", fallback=50))
print("Milliseconds between measurements: " + str(msBetweenMeasurements))

# Set the number of measurements per PPMP message
measurementsPerMessage = os.getenv("MEASUREMENTS_PER_MESSAGE", config.getint("DeviceSettings", "MeasurementsPerMessage", fallback=100))
print("Measurements per message: " + str(measurementsPerMessage))

# Set the ID of the device
deviceId = os.getenv("DEVICE_ID", config.get("DeviceSettings", "DeviceID", fallback=("drone" + str(r.randint(1,1000)))))
print("Device ID: " + deviceId)

# Template definition
templateDefinition = os.getenv("VALUES_TEMPLATE_LOC", config.get("DeviceSettings", "ValuesTemplateLocation", fallback="template.json"))
print("Template definition location: " + templateDefinition)

# Template definition as raw json
templateDefinitionVal = os.getenv("VALUES_TEMPLATE_VAL", None)
print("Template definition value: " + str(templateDefinitionVal))

device = Device(deviceId)

currentSeries = []
currentSeriesNames = []
if templateDefinition or templateDefinitionVal:
    if(templateDefinitionVal):
        templateData = json.load(templateDefinitionVal)
    elif(templateDefinition):
        with open(templateDefinition) as f:
            templateData = json.load(f)

    for definition in templateData:
        currentSeriesNames.append(definition["name"])
        currentSeries.append(ValueTemplate(definition["name"], definition["min"], definition["max"]))

else:
    currentSeries.append(ValueTemplate("temperature", 10, 40))
    currentSeries.append(ValueTemplate("pressure", 950, 1100))
    currentSeries.append(ValueTemplate("humidity", 20, 90))


m = Measurement(unide.process.local_now(), dimensions=currentSeriesNames)
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
    newMetrics = dict()
    for val in currentSeries:
        newMetrics[val.name] = r.randint(val.min, val.max)
    m.add_sample(unide.process.local_now(), **newMetrics)

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
