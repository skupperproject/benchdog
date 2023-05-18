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

    # Find the middlest result by average latency for each scenario

    for scenario_data in data.values():
        try:
            latency_averages = [x["latency"]["average"] for x in scenario_data]
        except KeyError:
            continue

        index = latency_averages.index(_statistics.median_low(latency_averages))

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

    if operation_text is not None:
        print(operation_text)

    print("Throughput is the number of operations per second (ops/s).")

    print("Latency is the duration of an operation in milliseconds (ms).")
    print("High and low results (by average latency) from repeated runs are discarded.")
    print()
