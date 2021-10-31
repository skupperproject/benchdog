from plano import *

import numpy as _numpy

def summarize(data):
    summary = dict()

    for config in ("1", "10", "100"):
        results = data[config]
        throughputs = [x["operations"] / x["duration"] for x in results]
        throughput = _numpy.percentile(throughputs, 50, interpolation="nearest")
        index = throughputs.index(throughput)
        result = results[index]

        summary[config] = {
            "throughput": round(throughput, 2),
            "latency": result["latency"],
        }

    return summary
