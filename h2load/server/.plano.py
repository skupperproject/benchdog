from plano import *

image_tag = "quay.io/ssorj/benchdog-h2load-server"

@command
def build():
    run(f"podman build -t {image_tag} .")

@command(name="run")
def run_():
    build()
    run(f"podman run --net host --rm {image_tag}")

@command
def push():
    build()
    run(f"podman push {image_tag}")
