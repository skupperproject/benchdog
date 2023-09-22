import json as _json
import numpy as _numpy

from plano import *

def load_config(default_port=8080):
    return Namespace(host=ENV.get("BENCHDOG_HOST", "localhost"),
                     port=ENV.get("BENCHDOG_PORT", default_port),
                     tls=ENV.get("BENCHDOG_TLS", "0") == "1",
                     duration=int(ENV.get("BENCHDOG_DURATION", 60)),
                     iterations=int(ENV.get("BENCHDOG_ITERATIONS", 1)))

def report(config, data, operation_text=None):
    print()
    print("## Configuration")
    print()

    if config.tls:
        tls_state = "enabled"
    else:
        tls_state = "disabled"

    print(f"Host:        {config.host}")
    print(f"Port:        {config.port}")
    print(f"TLS:         {tls_state}")
    print(f"Duration:    {config.duration} {plural('second', config.duration)}")
    print(f"Iterations:  {config.iterations}")

    # print()
    # print("## Data")
    # print()

    # print(_json.dumps(data))

    results = dict()

    for scenario in (10, 100, 500):
        scenario_data = data[scenario]

        latencies = [x["latency"]["average"] for x in scenario_data]

        latency = _numpy.percentile(latencies, 50, interpolation="nearest")
        index = latencies.index(latency)
        result = scenario_data[index]

        results[scenario] = {
            "throughput": round(result["operations"] / result["duration"], 2),
            "latency": result["latency"],
        }

    columns = "{:>11}  {:>18}  {:>14}  {:>14}  {:>14}"

    print()
    print("## Results")
    print()

    print(columns.format("CONNECTIONS", "THROUGHPUT", "LATENCY AVG", "LATENCY P50", "LATENCY P99"))

    for scenario in (10, 100, 500):
        try:
            result = results[scenario]
        except KeyError:
            continue

        latency = result["latency"]

        print(columns.format(scenario,
                             "{:,.1f} ops/s".format(result["throughput"]),
                             "{:,.3f} ms".format(latency["average"]),
                             "{:,.3f} ms".format(latency["p50"]),
                             "{:,.3f} ms".format(latency["p99"])))

    print()

    if operation_text is not None:
        print(operation_text)

    print("Throughput is the number of operations per second.")
    print("Latency is the duration of an operation in milliseconds.")
    print("High and low results from repeated runs are discarded.")
    print()
