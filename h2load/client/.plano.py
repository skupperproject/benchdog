from plano import *

image_tag = "quay.io/ssorj/benchdog-h2load-client"

@command
def build():
    run(f"podman build -t {image_tag} .")

@command
def run_(host="localhost", port=58080, duration=10, iterations=1):
    build()
    run(f"podman run --net host --rm"
        f" --env BENCHDOG_HOST={host} --env BENCHDOG_PORT={port}"
        f" --env BENCHDOG_DURATION={duration}  --env BENCHDOG_ITERATIONS={iterations}"
        f" {image_tag}")

@command
def push():
    build()
    run(f"podman push {image_tag}")
