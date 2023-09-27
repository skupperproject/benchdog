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
import pandas as _pandas

from benchdog import *

def run_client(config, connections, rate):
    args = [
        "pgbench",
        "--client", connections,
        "--rate", connections * rate,
        "--time", config.duration,
        "--host", config.host,
        "--port", config.port,
        "--jobs", 10,
        "--progress", 2,
        "--protocol", "prepared",
        "--select-only",
        "--log",
    ]

    run("rm -f pgbench_log*", shell=True)
    run(args)

    return process_output()

def process_output():
    run("cat pgbench_log.* > pgbench_log", shell=True)

    if get_file_size("pgbench_log") == 0:
        raise Exception("No data in pgbench logs")

    # 0: client_id
    # 1: transaction_no
    # 2: time (the transaction's elapsed time in microseconds)
    # 3: script_no
    # 4: time_epoch (the transaction's completion time as an epoch timestamp (seconds))
    # 5: time_us (the fractional extension to time_epoch, in microseconds)
    # 6: schedule_lag (the transaction's start delay in microseconds)

    data = _pandas.read_table("pgbench_log", sep=" ", header=None, dtype="int")
    data = data.sort_values([4, 5])

    first = data.head(1).iloc[0]
    last = data.tail(1).iloc[0]

    start_time = (first[4] + first[5] / 1_000_000) - first[2] / 1_000_000
    end_time = last[4] + last[5] / 1_000_000

    duration = end_time - start_time
    operations = len(data)
    latencies = data[2] + data[6] # Transaction time + start delay
    average = latencies.mean()
    percentiles = latencies.quantile(0.5), latencies.quantile(0.99)

    data = {
        "duration": round(duration, 3),
        "operations": operations,
        "latency": {
            "average": round(average / 1000, 3),
            "p50": round(percentiles[0] / 1000, 3),
            "p99": round(percentiles[1] / 1000, 3),
        },
    }

    return data

def run_scenario(config, connections, rate):
    results = list()

    for i in range(config.iterations):
        sleep(min((10, config.duration)))
        results.append(run_client(config, connections, rate))

    return results

def main():
    ENV["PGUSER"] = "postgres"
    ENV["PGPASSWORD"] = "c66efc1638e111eca22300d861c8e364"

    config = load_config(default_port=55432)

    await_port(config.port, host=config.host)

    while True:
        sleep(1)

        try:
            run(f"psql --host {config.host} --port {config.port} --command '\d pgbench_accounts'", output=DEVNULL)
        except PlanoProcessError:
            continue
        else:
            break

    scenarios = list()
    results = dict()

    for scenario_spec in config.scenarios.split(","):
        scenarios.append(map(int, scenario_spec.split(":", 1)))

    for connections, rate in scenarios:
        results[f"{connections}:{rate}"] = run_scenario(config, connections, rate)

    report(config, results, operation_text="Each operation is a SQL select.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
