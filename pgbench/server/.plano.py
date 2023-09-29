from plano import *

image_tag = "quay.io/skupper/benchdog-pgbench-server"

@command
def build():
    run(f"podman build -t {image_tag} .")

@command
def run_():
    build()
    run(f"podman run --rm -p 55432:55432 {image_tag}")

@command
def push():
    build()
    run(f"podman push {image_tag}")
