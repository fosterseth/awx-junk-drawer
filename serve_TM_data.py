from benchmark_task_manager import *
import itertools
iteration = 1
TM = [0,2]
toggle = itertools.cycle(TM)
while True:
    t1 = time.time()
    z = next(toggle)
    eval('TaskManager{0}()._schedule()'.format(z))
    groupid = z
    elapsed = time.time() - t1
    with open("tm_dump", "w") as fid:
        fid.write("{0},{1},{2}".format(elapsed, groupid, iteration))

    iteration += 1
    time.sleep(1)
