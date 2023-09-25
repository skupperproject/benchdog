import json as _json

from benchdog import *

config = load_config(default_port=55672)

def run_client(connections, rate):
    output_dir = make_temp_dir()

    args = [
        "qbench", "client",
        "--connections", connections,
        "--rate", rate,
        "--duration", config.duration,
        "--host", config.host,
        "--port", config.port,
        "--output", output_dir,
    ]

    run("rm -f qbench.log*", shell=True)
    run(args)

    return process_output(output_dir)

def process_output(output_dir):
    data = read_json(join(output_dir, "summary.json"))

    scenario_key = str(data["configuration"]["connections"])

    return data["scenarios"][scenario_key]

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

    report(config, results, operation_text="Each operation is two AMQP message transfers.")
