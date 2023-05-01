from plano import *

@command
def bench_configs():
    def run_config(routers, cpus):
        #
        run("kubectl config set-context --current --namespace bds")
        run("skupper delete", check=False)
        sleep(5)
        run(f"skupper init") # --routers {routers} --router-cpu-limit {cpus}")
        sleep(5)
        run("skupper token create /tmp/a.yaml")
        run("skupper expose deployment/pgbench-server --port 5432")
        # run("skupper expose deployment/wrk-server --port 8080")

        sleep(10)

        run("kubectl config set-context --current --namespace bdc")
        run("skupper delete", check=False)
        sleep(5)
        run(f"skupper init") # --routers {routers} --router-cpu-limit {cpus}")
        sleep(5)
        run("skupper link create /tmp/a.yaml")

        sleep(60)

        run("kubectl run -it --rm --env BENCHDOG_HOST=pgbench-server --image quay.io/ssorj/benchdog-pgbench-client pgbench-client")
        # run("kubectl run -it --rm --env BENCHDOG_HOST=wrk-server --image quay.io/ssorj/benchdog-wrk-client wrk-client")

    # run_config(1, 4)
    # run_config(1, 2)
    run_config(1, 1)
    # run_config(2, 1)
    # run_config(2, 0.5)

@command
def clean():
    remove(find(".", "__pycache__"))
