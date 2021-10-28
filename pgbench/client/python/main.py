from plano import *

ENV["PGUSER"] = "postgres"
ENV["PGPASSWORD"] = "postgres"

host = ENV.get("BENCHDOG_SERVER_HOST", "localhost")
port = ENV.get("BENCHDOG_SERVER_PORT", "5432")

await_port(port, host=host)

def run_pgbench(scale):
    args = [
        "pgbench",
        "--jobs", str(scale),
        "--client", str(scale),
        "--time", ENV.get("BENCHDOG_DURATION", "10"),
        "--host", host,
        "--port", port,
        "--progress", "2",
        "--select-only",
        "--log",
    ]

    run(args)

run_pgbench(1)
run_pgbench(10)
run_pgbench(100)

    # f"pgbench --jobs {scale} --client {scale} --time {duration} --host 5ddcad63-us-east.lb.appdomain.cloud --port 5432 --progress 2 --select-only --log")
