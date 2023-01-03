import sys
import subprocess
from time import sleep
from multiprocessing import shared_memory

tokens = shared_memory.ShareableList([0 for _ in range(10)])

subprocess.Popen([sys.executable, "test1.py", tokens.shm.name])

while True:
    for i, v in enumerate(range(100, 110)):
        tokens[i] = v
        sleep(1)
    sleep(20)
    break
tokens.shm.close()
tokens.shm.unlink()
del tokens
