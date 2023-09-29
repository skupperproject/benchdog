from plano import *

@command
def clean():
    remove(find(".", "__pycache__"))
