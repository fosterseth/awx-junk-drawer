import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import time

plt.ion()
fig = plt.figure()
tm_data = np.array([[0,0]])
tm_data_color = [0]
ax = fig.add_subplot(111)

scatter1 = ax.scatter(0, 0)

plt.set_cmap('jet')
colors = [0,.6,.3,1]



last_iteration = None

while True:
    with open("tm_dump", "r") as fid:
        raw_data = fid.read()
    raw_data = raw_data.split(',')
    elapsed_time = float(raw_data[0])
    groupid = int(raw_data[1])
    iteration = int(raw_data[2])
    if iteration != last_iteration:
        last_iteration = iteration
        tm_data = np.append(tm_data, np.array([[float(iteration), elapsed_time]]), axis=0)
        tm_data_color.append(colors[groupid])
        scatter1.set_offsets(tm_data)
        xmin=tm_data[1:,0].min(); xmax=tm_data[1:,0].max()
        ymin=tm_data[1:,1].min(); ymax=tm_data[1:,1].max()
        ax.set_xlim(xmin-0.1*(xmax-xmin),xmax+0.1*(xmax-xmin))
        # ax.set_ylim(ymin-0.1*(ymax-ymin),ymax+0.1*(ymax-ymin))
        ax.set_ylim(-1,15)
        scatter1.set_array(np.array(tm_data_color))
        fig.canvas.draw()
        fig.canvas.flush_events()
    plt.pause(.5)
