#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
#

import json as _json
import statistics as _statistics

from benchdog import *

def run_client(config, connections, rate):
    args = [
        "h2load", f"http://{config.host}:{config.port}/index.txt",
        "--clients", connections,
        "--rps", rate,
        "--duration", config.duration,
        "--warm-up-time", 5,
        "--threads", min(10, connections),
        "--max-concurrent-streams", 10,
    ]

    with temp_file() as f:
        run(args, output=f)

        print(read(f))

        return process_output(config, f)

def process_output(config, output_file):
    output = read_lines(output_file)

    for line in output:
        if line.startswith("traffic:"):
            bits = int(line.split()[2][1:-1]) * 8
            break
    else:
        raise Exception(output)

    for line in output:
        if line.startswith("requests:"):
            operations = int(line.split()[1])
            break
    else:
        raise Exception(output)

    for line in output:
        if line.startswith("time for request:"):
            items = line.split()
            max_latency = convert(items[4])
            average_latency = convert(items[5])
            break
    else:
        raise Exception(output)

    results = {
        "duration": config.duration,
        "operations": operations,
        "bits": bits, # bytes?
        "latency": {
            "average": average_latency,
            "max": max_latency,
        }
    }

    return results

def convert(value):
    if value.endswith("us"):
        return float(value.removesuffix("us")) / 1000

    if value.endswith("ms"):
        return float(value.removesuffix("ms"))

    if value.endswith("s"):
        return float(value.removesuffix("s")) * 1000

    raise Exception()

def run_scenario(config, connections, rate):
    results = list()

    for i in range(config.iterations):
        sleep(min((10, config.duration)))
        results.append(run_client(config, connections, rate))

    return results

def report(config, results, operation_text=None):
    print()
    print("## Configuration")
    print()

    print(f"Host:        {config.host}")
    print(f"Port:        {config.port}")
    print(f"Scenarios:   {config.scenarios}")
    print(f"Duration:    {config.duration} {plural('second', config.duration)}")
    print(f"Iterations:  {config.iterations}")

    print()
    print("## Data")
    print()

    print_json(results)

    summary = dict()

    for scenario, result in results.items():
        latencies = [x["latency"]["average"] for x in result]

        latency = _statistics.median_high(latencies)
        index = latencies.index(latency)
        result = result[index]

        summary[scenario] = {
            "throughput": round(result["operations"] / result["duration"], 2),
            "latency": result["latency"],
        }

    columns = "{:>11}  {:>18}  {:>14}  {:>14}"

    print()
    print("## Results")
    print()

    print(columns.format("CONNECTIONS", "THROUGHPUT", "LATENCY AVG", "LATENCY MAX"))

    for scenario, result in summary.items():
        latency = result["latency"]
        connections, rate = scenario.split(":", 1)

        print(columns.format(connections,
                             "{:,.1f} ops/s".format(result["throughput"]),
                             "{:,.3f} ms".format(latency["average"]),
                             "{:,.3f} ms".format(latency["max"])))

    print()

    if operation_text is not None:
        print(operation_text)

    print("Throughput is the number of operations per second.")
    print("Latency is the duration of an operation in milliseconds.")
    print("High and low results from repeated runs are discarded.")
    print()

def main():
    config = load_config(default_port=58080)

    await_port(config.port, host=config.host)

    scenarios = list()
    results = dict()

    for scenario_spec in config.scenarios.split(","):
        scenarios.append(map(int, scenario_spec.split(":", 1)))

    for connections, rate in scenarios:
        results[f"{connections}:{rate}"] = run_scenario(config, connections, rate)

    report(config, results, operation_text="Each operation is an HTTP/2 request.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
