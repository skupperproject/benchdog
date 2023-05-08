import json as _json
import statistics as _statistics

from plano import *

def load_config(default_port=8080):
    return Namespace(host=ENV.get("BENCHDOG_HOST", "localhost"),
                     port=ENV.get("BENCHDOG_PORT", default_port),
                     duration=int(ENV.get("BENCHDOG_DURATION", 60)),
                     iterations=int(ENV.get("BENCHDOG_ITERATIONS", 5)))

def print_config(config):
    print()
    print("## Configuration")
    print()

    print(f"Host:        {config.host}")
    print(f"Port:        {config.port}")
    print(f"Duration:    {config.duration} {plural('second', config.duration)}")
    print(f"Iterations:  {config.iterations}")

def report(config, data, scenario_text=None, job_text=None, operation_text=None):
    print_config(config)

    print()
    print("## Data")
    print()

    print(_json.dumps(data, indent=2))

    results = list()

    for scenario_data in data.values():
        # Find the middlest result by throughput

        try:
            throughputs = [x["operations"] / x["duration"] for x in scenario_data]
        except KeyError:
            continue

        index = throughputs.index(_statistics.median_low(throughputs))

        results.append(scenario_data[index])

    columns = "{:>8}  {:>6}  {:>18}  {:>14}  {:>14}  {:>14}"

    print()
    print("## Results")
    print()

    print(columns.format("SCENARIO", "JOBS", "THROUGHPUT", "LATENCY AVG", "LATENCY 50%", "LATENCY 99%"))

    for scenario, data in enumerate(results, 1):
        throughput = data["operations"] / data["duration"]
        latency = data["latency"]

        print(columns.format(scenario,
                             data["jobs"],
                             "{:,.2f} ops/s".format(throughput),
                             "{:,.2f} ms".format(latency["average"]),
                             "{:,.2f} ms".format(latency["50"]),
                             "{:,.2f} ms".format(latency["99"])))

    print()

    if scenario_text is not None:
        print(scenario_text)

    if job_text is not None:
        print(job_text)

    print("Throughput is the number of operations per second (ops/s).")

    if operation_text is not None:
        print(operation_text)

    print("Latency is the duration of an operation in milliseconds (ms).")
    print("High and low results from repeated runs are discarded.")
    print()
