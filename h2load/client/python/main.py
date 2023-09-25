import json as _json

from benchdog import *

config = load_config(default_port=58080)

def run_client(connections, rate):
    args = [
        "h2load", f"http://{config.host}:{config.port}/index.txt",
        "--clients", connections,
        "--rps", rate,
        "--duration", config.duration,
        "--threads", min(4, connections),
        "--max-concurrent-streams", 10,
    ]

    with temp_file() as f:
        run(args, output=f)

        print(read(f))

        return process_output(f)

def process_output(output_file):
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
            max_latency = items[4]
            average_latency = items[5]
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

def run_scenario(connections, rate):
    results = list()

    for i in range(config.iterations):
        sleep(min((10, config.duration)))
        results.append(run_client(connections, rate))

    return results

if __name__ == "__main__":
    await_port(config.port, host=config.host)

    scenarios = list()
    results = dict()

    for scenario_spec in config.scenarios.split(","):
        scenarios.append(map(int, scenario_spec.split(":", 1)))

    for connections, rate in scenarios:
        results[f"{connections}:{rate}"] = run_scenario(connections, rate)

    pprint(results)

    # report(config, results, operation_text="Each operation is an HTTP/2 request.")
