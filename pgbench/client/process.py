#!/usr/bin/python

import glob as _glob
import json as _json
import numpy as _numpy
import sys as _sys

dtype = [
    ("client_id", _numpy.uint64),
    ("transaction_no", _numpy.uint64),
    ("time", _numpy.uint64),
    ("script_no", _numpy.uint64),
    ("time_epoch", _numpy.uint64),
    ("time_us", _numpy.uint64),
]

records = _numpy.loadtxt(_sys.argv[1], dtype=dtype)
records.sort(order=("time_epoch", "time_us"))

start_time = records[0][4] + records[0][5] / 1000000 - records[0][2] / 1000000
end_time = records[-1][4] + records[-1][5] / 1000000

duration = end_time - start_time
operations = len(records)
throughput = operations / duration

latencies = records["time"]
average = _numpy.mean(latencies)
percentiles = _numpy.percentile(latencies, (50, 99))

data = {
    "duration": round(duration, 2),
    "operations": operations,
    "throughput": round(throughput, 2),
    "latency": {
        "average": round(average / 1000, 2),
        "50": round(percentiles[0] / 1000, 2),
        "99": round(percentiles[1] / 1000, 2),
    },
}

print(_json.dumps(data))
