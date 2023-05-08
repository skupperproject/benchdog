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

def run_kbench(config, jobs):
    remove(list_dir(".", "kbench.log*"), quiet=True)

    args = [
        # "taskset", "--cpu-list", "0-7",
        "java", "-jar", "target/client-1.0.0-SNAPSHOT-jar-with-dependencies.jar",
        str(config.host),
        str(config.port),
        str(config.duration),
        str(jobs),
    ]

    run(args)

    data = process_kbench_logs()
    data["jobs"] = jobs

    return data

def process_kbench_logs():
    run("cat kbench.log.* > kbench.log", shell=True)

    if get_file_size("kbench.log") == 0:
        raise Exception("No data in logs")

    data = _pandas.read_csv("kbench.log", header=None)

    start_time = data[0].min() / 1_000_000
    end = data.loc[data[0].idxmax()]
    end_time = (end[0] + end[1]) / 1_000_000

    duration = end_time - start_time
    operations = len(data)

    average = data[1].mean() / 1000
    p50 = data[1].quantile(0.5) / 1000
    p99 = data[1].quantile(0.99) / 1000

    data = {
        "duration": round(duration, 2),
        "operations": operations,
        "latency": {
            "average": round(average, 2),
            "50": round(p50, 2),
            "99": round(p99, 2),
        },
    }

    return data

def run_scenario(config, jobs):
    results = list()

    for i in range(config.iterations):
        sleep(min((10, config.duration)))
        results.append(run_kbench(config, jobs))

    return results

def main():
    config = load_config(default_port=9092)

    print_config(config)

    await_port(config.port, host=config.host)

    data = {
        1: run_scenario(config, 1),
        2: run_scenario(config, 10),
        3: run_scenario(config, 100),
    }

    report(config, data,
           scenario_text="Each scenario uses a single Kafka producer sending 10,000 records per second.",
           job_text="Each job is a Kafka consumer.",
           operation_text="Each operation is a Kafka record consumed.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
