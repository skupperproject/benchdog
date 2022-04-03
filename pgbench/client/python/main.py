import json as _json
import numpy as _numpy

from benchdog import *

ENV["PGUSER"] = "postgres"
ENV["PGPASSWORD"] = "c66efc1638e111eca22300d861c8e364"

config = load_config(default_port=5432)

def run_pgbench(clients):
    args = [
        "pgbench",
        "--jobs", str(clients),
        "--client", str(clients),
        "--host", str(config.host),
        "--port", str(config.port),
        "--time", str(config.duration),
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
        raise Exception("No data in pgbench logs")

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

def run_scenario(clients):
    results = list()

    for i in range(config.iterations):
        sleep(min((10, config.duration)))
        results.append(run_pgbench(clients))

    return results

if __name__ == "__main__":
    await_port(config.port, host=config.host)

    while True:
        sleep(1)

        try:
            run(f"psql --host {config.host} --port {config.port} --command '\d pgbench_accounts'", output=DEVNULL)
        except PlanoProcessError:
            continue
        else:
            break

    data = {
        "1": run_scenario(1),
        "10": run_scenario(10),
        "100": run_scenario(100),
    }

    report(config, data, operation_text="Each operation is a SQL select.")
