from plano import *

@command
def build():
    run("gcc qbench-server.c -o qbench-server -g -O2 -std=c99 -fno-omit-frame-pointer -lqpid-proton-core -lqpid-proton-proactor")
