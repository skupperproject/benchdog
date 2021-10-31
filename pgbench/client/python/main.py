import json as _json
import numpy as _numpy

from benchdog import *

ENV["PGUSER"] = "postgres"
ENV["PGPASSWORD"] = "c66efc1638e111eca22300d861c8e364"

host = ENV.get("BENCHDOG_SERVER_HOST", "localhost")
port = ENV.get("BENCHDOG_SERVER_PORT", "5432")
duration = int(ENV.get("BENCHDOG_DURATION", 10))
iterations = int(ENV.get("BENCHDOG_ITERATIONS", 5))

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

    run("rm -f pgbench_log*", shell=True)
    run(args)

    return process_pgbench_logs()

def process_pgbench_logs():
    run("cat pgbench_log.* > pgbench_log", shell=True)

    if get_file_size("pgbench_log") == 0:
        return

    dtype = [
        ("client_id", _numpy.uint64),
        ("transaction_no", _numpy.uint64),
        ("time", _numpy.uint64),
        ("script_no", _numpy.uint64),
        ("time_epoch", _numpy.uint64),
        ("time_us", _numpy.uint64),
    ]

    records = _numpy.loadtxt("pgbench_log", dtype=dtype)

    records.sort(order=("time_epoch", "time_us"))

    start_time = records[0][4] + records[0][5] / 1000000 - records[0][2] / 1000000
    end_time = records[-1][4] + records[-1][5] / 1000000

    duration = end_time - start_time
    operations = len(records)
    latencies = records["time"]
    average = _numpy.mean(latencies)
    percentiles = _numpy.percentile(latencies, (50, 99))

    data = {
        "duration": round(duration, 2),
        "operations": operations,
        "latency": {
            "average": round(average / 1000, 2),
            "50": round(percentiles[0] / 1000, 2),
            "99": round(percentiles[1] / 1000, 2),
        },
    }

    return data

def run_config(clients):
    results = list()

    for i in range(iterations):
        sleep(min((10, duration)))
        results.append(run_pgbench(clients))

    return results

if __name__ == "__main__":
    await_port(port, host=host)

    while True:
        sleep(1)

        try:
            run(f"psql --host {host} --port {port} --command '\d pgbench_accounts'", output=DEVNULL)
        except PlanoProcessError:
            continue
        else:
            break

    result = {
        "1": run_config(1),
        "10": run_config(10),
        "100": run_config(100),
    }

    print(emit_json(summarize(result)))
