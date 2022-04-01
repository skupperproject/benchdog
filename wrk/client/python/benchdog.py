import json as _json
import numpy as _numpy

from plano import *

def load_config(default_port=8080):
    return Namespace(host=ENV.get("BENCHDOG_HOST", "localhost"),
                     port=ENV.get("BENCHDOG_PORT", default_port),
                     tls=ENV.get("BENCHDOG_TLS", "0") == "1",
                     duration=int(ENV.get("BENCHDOG_DURATION", 60)),
                     iterations=int(ENV.get("BENCHDOG_ITERATIONS", 5)))

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

    for scenario in ("1", "10", "100"):
        scenario_data = data[scenario]

        try:
            throughputs = [x["operations"] / x["duration"] for x in scenario_data]
        except KeyError:
            continue

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
        try:
            result = results[scenario]
        except KeyError:
            continue

        latency = result["latency"]

        print(columns.format(scenario,
                             "{:,.2f}".format(result["throughput"]),
                             "{:,.2f}".format(latency["average"]),
                             "{:,.2f}".format(latency["50"]),
                             "{:,.2f}".format(latency["99"])))

    print()

    if operation_text is not None:
        print(operation_text)

    print("Throughput is the number of operations per second.")
    print("Latency is the duration of an operation in milliseconds.")
    print("High and low results from repeated runs are discarded.")
    print()
