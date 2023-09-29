from plano import *

image_tag = "quay.io/skupper/benchdog-h2load-server"

@command
def build(no_cache=False):
    no_cache = "--no-cache" if no_cache else ""
    run(f"podman build -t {image_tag} {no_cache} .")

@command
def run_():
    build()
    run(f"podman run --net host --rm {image_tag}")

@command
def push():
    build()
    run(f"podman push {image_tag}")
