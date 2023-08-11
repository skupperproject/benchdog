from plano import *

@command
def run_():
    with working_dir("client"):
        run("plano build")

    with working_dir("server"):
        run("plano build")

    server = start("server/qbench-server")

    client = start("client/qbench-client")

    sleep(5)

    kill(client)
    kill(server)

    wait(client)
    wait(server)

    run("cat qbench.*.log > qbench.log", shell=True)

    count = call("wc -l qbench.log", shell=True).split()[0]

    print()
    print(">>> {:,} messages per second <<<".format(int(count) / 5))
    print()
