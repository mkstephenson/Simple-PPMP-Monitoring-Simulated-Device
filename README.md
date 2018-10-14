# Simulated PPMP Device
This script will simulate a device which sends metrics regularly to a target server. The following is configurable:

|Parameter|Environment Variable|Configuration Section|Configuration Parameter|Configuration Fallback|
|---|---|---|---|---|
|Monitoring Endpoint|MONITORING_ENDPOINT|ConnectionSettings|MonitoringEndpoint|https://example.com/|
|HTTP Authorization Header|AUTH_HEADER|ConnectionSettings|AuthHeader|None|
|Maximum Number of Retries|MAX_RETRIES|ConnectionSettings|MaxRetries|10|
|Timeout|TIMEOUT|ConnectionSettings|Timeout|30|
|Milliseconds between measurements|MS_BETWEEN_MEASUREMENTS|DeviceSettings|MSBetweenMeasurements|50|
|Measurements per message|MEASUREMENTS_PER_MESSAGE|DeviceSettings|MeasurementsPerMessage|100|
|Device ID|DEVICE_ID|DeviceSettings|DeviceID|drone with random number between 1 and 1000|
|Location of template for values|VALUES_TEMPLATE_LOC|DeviceSettings|ValuesTemplateLocation|template.json|
|JSON of template for values|VALUES_TEMPLATE_VAL|-|-|-|