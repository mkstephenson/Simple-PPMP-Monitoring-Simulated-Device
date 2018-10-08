import time
import datetime
from datetime import timedelta
from random import Random

import unide
import requests
from requests_futures.sessions import FuturesSession
from unide.measurement import *

monitoringEndpoint = "http://192.168.1.136:5000"
authHeader = "Bearer iksldufgvuzdioasfvg"
msBetweenMeasurements = 250
measurementsPerMessage = 50

device = Device("rpidrone1")

r = Random()

currentSeries = ["temperature", "humidity", "pressure"]

m = Measurement(unide.process.local_now(), dimensions=currentSeries)
a = requests.adapters.HTTPAdapter(max_retries=50)
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
        result = session.post(monitoringEndpoint, data=content, background_callback=bg_cb)

        # Reset measurement object
        m = Measurement(unide.process.local_now(), dimensions=currentSeries)

    time.sleep(((lastMeasurement + timedelta(
        milliseconds=msBetweenMeasurements)) - datetime.datetime.utcnow()).total_seconds())
