from plano import *

@command
def run_():
    kafka_dir = f"{get_home_dir()}/kafka"

    with working_dir(kafka_dir):
        with start("bin/zookeeper-server-start.sh config/zookeeper.properties"):
            sleep(2)

            with start("bin/kafka-server-start.sh config/server.properties"):
                while True:
                    sleep(2)
