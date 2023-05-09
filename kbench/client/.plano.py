from plano import *

image_tag = "quay.io/ssorj/benchdog-kbench-client"

@command
def build():
    run("mvn package")

@command(name="run")
def run_():
    build()
    run("python python/main.py")

@command
def clean():
    run("mvn clean")
    remove(list_dir(".", "kbench.log*"))
    remove("__pycache__")

@command
def build_image():
    clean()
    build()
    run(f"podman build -t {image_tag} .")

@command
def run_image():
    build_image()
    run(f"podman run -it --net host {image_tag}")

@command
def push_image():
    build_image()
    run(f"podman push {image_tag}")
