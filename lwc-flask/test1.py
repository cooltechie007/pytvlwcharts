import sys
from time import sleep
from multiprocessing import shared_memory

tokens = shared_memory.ShareableList(name=sys.argv[1])
while True:
    print(tokens)
    if tokens[-1] == 109:
        tokens.shm.close()
        tokens.shm.unlink()
        break
    else:
        sleep(1)
