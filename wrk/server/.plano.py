from plano import *

image_tag = "quay.io/skupper/benchdog-wrk-server"

@command
def build():
    run(f"podman build -t {image_tag} .")

@command
def run_():
    build()
    run(f"podman run --net host --rm {image_tag}")

@command
def push():
    build()
    run(f"podman push {image_tag}")
