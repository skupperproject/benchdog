from plano import *

image_tag = "quay.io/ssorj/benchdog-qbench-server"

@command
def build():
    run(f"podman build -t {image_tag} .")

@command(name="run")
def run_():
    build()
    run(f"podman run --rm -p 55672:55672 {image_tag}")

@command
def push():
    build()
    run(f"podman push {image_tag}")
