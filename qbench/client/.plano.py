from plano import *

@command
def build():
    run("gcc qbench-client.c -o qbench-client -g -O2 -std=c99 -fno-omit-frame-pointer -lqpid-proton -lqpid-proton-proactor")
