import json as _json
import numpy as _numpy

from plano import *

ENV["PGUSER"] = "postgres"
ENV["PGPASSWORD"] = "c66efc1638e111eca22300d861c8e364"

host = ENV.get("BENCHDOG_SERVER_HOST", "localhost")
port = ENV.get("BENCHDOG_SERVER_PORT", "5432")
duration = int(ENV.get("BENCHDOG_DURATION", 10))
iterations = int(ENV.get("BENCHDOG_ITERATIONS", 5))

await_port(port, host=host)

def run_pgbench(clients):
    args = [
        "pgbench",
        "--jobs", str(clients),
        "--client", str(clients),
        "--host", host,
        "--port", port,
        "--time", str(duration),
        "--progress", "2",
        "--select-only",
        "--log",
    ]

    run(args)

def process_pgbench_logs(file, clients):
    dtype = [
        ("client_id", _numpy.uint64),
        ("transaction_no", _numpy.uint64),
        ("time", _numpy.uint64),
        ("script_no", _numpy.uint64),
        ("time_epoch", _numpy.uint64),
        ("time_us", _numpy.uint64),
    ]

    records = _numpy.loadtxt(file, dtype=dtype)
    records.sort(order=("time_epoch", "time_us"))

    start_time = records[0][4] + records[0][5] / 1000000 - records[0][2] / 1000000
    end_time = records[-1][4] + records[-1][5] / 1000000

    duration = end_time - start_time
    operations = len(records)
    throughput = operations / duration

    latencies = records["time"]
    average = _numpy.mean(latencies)
    percentiles = _numpy.percentile(latencies, (50, 99))

    data = {
        "clients": clients,
        "duration": round(duration, 2),
        "operations": operations,
        "throughput": round(throughput, 2),
        "latency": {
            "average": round(average / 1000, 2),
            "50": round(percentiles[0] / 1000, 2),
            "99": round(percentiles[1] / 1000, 2),
        },
    }

    append("results", _json.dumps(data) + "\n")

def run_config(clients):
    remove("results")

    for i in range(iterations):
        sleep(duration)
        run_pgbench(clients)
        run("cat pgbench_log.* > pgbench_log", shell=True)

        if get_file_size("pgbench_log") != 0:
            process_pgbench_logs("pgbench_log", clients)

        run("rm pgbench_log*", shell=True)

    print()
    print("XXX 1")

    print(read("results"))

    print("XXX 2")

    results = list()
    throughputs = list()

    with open("results") as f:
        for line in f:
            result = parse_json(line)
            results.append(result)
            throughputs.append(result["throughput"])

    index = throughputs.index(_numpy.percentile(throughputs, 50, interpolation="nearest"))

    result = results[index]

    print(result)

    append("report", _json.dumps(result) + "\n")

if __name__ == "__main__":
    run_config(1)
    run_config(10)
    run_config(100)
    print()
    print("XXX 3")
    print(read("report"))
