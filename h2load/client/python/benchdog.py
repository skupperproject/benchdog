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

from plano import *

def load_config(default_port=8080, default_scenarios="10:100,100:100,500:100"):
    return Namespace(host=ENV.get("BENCHDOG_HOST", "localhost"),
                     port=ENV.get("BENCHDOG_PORT", default_port),
                     scenarios=ENV.get("BENCHDOG_SCENARIOS", default_scenarios),
                     duration=int(ENV.get("BENCHDOG_DURATION", 60)),
                     iterations=int(ENV.get("BENCHDOG_ITERATIONS", 1)))

def report(config, results, operation_text=None):
    print()
    print("## Data")
    print()

    print_json(results)

    print()
    print("## Configuration")
    print()

    print(f"Host:        {config.host}")
    print(f"Port:        {config.port}")
    print(f"Scenarios:   {config.scenarios}")
    print(f"Duration:    {config.duration} {plural('second', config.duration)}")
    print(f"Iterations:  {config.iterations}")

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

    columns = "{:>11}  {:>18}  {:>14}  {:>14}  {:>14}"

    print()
    print("## Results")
    print()

    print(columns.format("CONNECTIONS", "THROUGHPUT", "LATENCY AVG", "LATENCY P50", "LATENCY P99"))

    for scenario, result in summary.items():
        latency = result["latency"]
        connections, rate = scenario.split(":", 1)

        print(columns.format(connections,
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
