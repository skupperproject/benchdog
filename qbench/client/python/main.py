import json as _json

from benchdog import *

config = load_config(default_port=55672)

def run_qbench(connections):
    output_dir = make_temp_dir()

    args = [
        "qbench", "client",
        "--output", output_dir,
        "--host", config.host,
        "--port", config.port,
        "--connections", connections,
        "--duration", config.duration,
        "--rate", 1000,
    ]

    run("rm -f qbench.log*", shell=True)
    run(args)

    return process_qbench_output(output_dir)

def process_qbench_output(output_dir):
    data = read_json(join(output_dir, "summary.json"))

    scenario_key = str(data["configuration"]["connections"])

    return data["scenarios"][scenario_key]

def run_scenario(connections):
    results = list()

    for i in range(config.iterations):
        sleep(min((10, config.duration)))
        results.append(run_qbench(connections))

    return results

if __name__ == "__main__":
    await_port(config.port, host=config.host)

    data = {
        1: run_scenario(1),
        10: run_scenario(10),
        100: run_scenario(100),
    }

    report(config, data, operation_text="Each operation is two AMQP messages, a request and a response.")
