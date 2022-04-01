import json as _json
import numpy as _numpy

from benchdog import *

config = load_config()

def run_wrk(clients):
    if config.tls:
        scheme = "https"
    else:
        scheme = "http"

    args = [
        "wrk",
        "--threads", str(clients),
        "--connections", str(clients),
        "--duration", str(config.duration),
        "--latency",
        "--script", "main.lua", # This writes to result.json
        f"{scheme}://{config.host}:{config.port}/",
    ]

    run(args)

    return read_json("result.json")

def run_scenario(clients):
    results = list()

    for i in range(config.iterations):
        sleep(min((10, config.duration)))
        results.append(run_wrk(clients))

    return results

if __name__ == "__main__":
    await_port(config.port, host=config.host)

    data = {
        "1": run_scenario(1),
        "10": run_scenario(10),
        "100": run_scenario(100),
    }

    report(config, data, operation_text="Each operation is an HTTP/1.1 GET request.")
