from plano import *

import json as _json
import numpy as _numpy

def load_config():
    return Namespace(host=ENV.get("BENCHDOG_SERVER_HOST", "localhost"),
                     port=ENV.get("BENCHDOG_SERVER_PORT", "8080"),
                     duration=int(ENV.get("BENCHDOG_DURATION", 10)),
                     iterations=int(ENV.get("BENCHDOG_ITERATIONS", 5)))

def report(config, data):
    print()
    print("## Configuration")
    print()

    print(f"Server: {config.host}:{config.port}")
    print(f"Duration: {config.duration} {plural('second', config.duration)}")
    print(f"Iterations: {config.iterations}")

    print()
    print("## Data")
    print()

    print(_json.dumps(data))

    results = dict()

    for scenario in ("1", "10", "100"):
        scenario_data = data[scenario]
        throughputs = [x["operations"] / x["duration"] for x in scenario_data]
        throughput = _numpy.percentile(throughputs, 50, interpolation="nearest")
        index = throughputs.index(throughput)
        result = scenario_data[index]

        results[scenario] = {
            "throughput": round(throughput, 2),
            "latency": result["latency"],
        }

    columns = "{:>7}  {:>12}  {:>12}  {:>12}  {:>12}"

    print()
    print("## Results")
    print()

    print(columns.format("CLIENTS", "THROUGHPUT", "LATENCY AVG", "LATENCY 50%", "LATENCY 99%"))

    for scenario in ("1", "10", "100"):
        result = results[scenario]
        latency = result["latency"]

        print(columns.format(scenario,
                             "{:,.2f}".format(result["throughput"]),
                             "{:,.2f}".format(latency["average"]),
                             "{:,.2f}".format(latency["50"]),
                             "{:,.2f}".format(latency["99"])))

    print()
    print("## Notes")
    print()

    print(" - Throughput is operations per second")
    print(" - Latencies are in milliseconds")

    print()
