from plano import *

@command
def build():
    run("mvn package")

@command(name="run")
def run_():
    build()
    run("java -jar /home/jross/code/benchdog/kafka/client/target/client-1.0.0-SNAPSHOT-jar-with-dependencies.jar 10 5")

@command
def clean():
    run("mvn clean")
    remove(list_dir(".", "output.log*"))
    remove("__pycache__")

@command
def build_image():
    build()
    run("podman build -t quay.io/ssorj/benchdog-kafka-client .")

@command
def run_image():
    build_image()
    run("podman run -it --net host quay.io/ssorj/benchdog-kafka-client")

@command
def push_image():
    build_image()
    run("podman push quay.io/ssorj/benchdog-kafka-client")
