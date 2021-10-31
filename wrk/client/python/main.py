import json as _json
import numpy as _numpy

from benchdog import *

host = ENV.get("BENCHDOG_SERVER_HOST", "localhost")
port = ENV.get("BENCHDOG_SERVER_PORT", "8080")
duration = int(ENV.get("BENCHDOG_DURATION", 10))
iterations = int(ENV.get("BENCHDOG_ITERATIONS", 5))

def run_wrk(clients):
    args = [
        "wrk",
        "--header", "'Connection: close'",
        "--threads", str(clients),
        "--connections", str(clients),
        "--duration", str(duration),
        "--latency",
        "--script", "main.lua", # This writes to result.json
        f"http://{host}:{port}/",
    ]

    run(args)

    return read_json("result.json")

def run_config(clients):
    results = list()

    for i in range(iterations):
        sleep(min((10, duration)))
        results.append(run_wrk(clients))

    return results

if __name__ == "__main__":
    await_port(port, host=host)

    result = {
        "1": run_config(1),
        "10": run_config(10),
        "100": run_config(100),
    }

    print(emit_json(summarize(result)))
