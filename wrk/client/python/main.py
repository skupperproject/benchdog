import json as _json
import numpy as _numpy

from benchdog import *

def run_client(config, connections, rate):
    args = [
        "wrk",
        "--connections", connections,
        "--duration", config.duration,
        "--threads", connections,
        "--latency",
        "--script", "main.lua", # This writes to result.json
        f"http://{config.host}:{config.port}/",
    ]

    run(args)

    return read_json("result.json")

def run_scenario(config, connections, rate):
    results = list()

    for i in range(config.iterations):
        sleep(min((10, config.duration)))
        results.append(run_client(config, connections, rate))

    return results

def main():
    config = load_config(default_port=58080)

    await_port(config.port, host=config.host)

    scenarios = list()
    results = dict()

    for scenario_spec in config.scenarios.split(","):
        scenarios.append(map(int, scenario_spec.split(":", 1)))

    for connections, rate in scenarios:
        results[f"{connections}:{rate}"] = run_scenario(config, connections, rate)

    report(config, results, operation_text="Each operation is an HTTP/1.1 GET request.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
