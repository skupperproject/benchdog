from plano import *

image_tag = "quay.io/skupper/benchdog-pgbench-client"

@command
def build():
    copy("../../common/benchdog.py", "python/benchdog.py")
    run(f"podman build -t {image_tag} .")

@command
def run_(host="localhost", port=55432, duration=10, iterations=1):
    build()
    run(f"podman run --net host --rm"
        f" --env BENCHDOG_HOST={host} --env BENCHDOG_PORT={port}"
        f" --env BENCHDOG_DURATION={duration}  --env BENCHDOG_ITERATIONS={iterations}"
        f" {image_tag}")

@command
def push():
    build()
    run(f"podman push {image_tag}")
