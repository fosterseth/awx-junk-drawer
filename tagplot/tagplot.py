"""
===============================================
Requirements
===============================================
"""

# pip install matplotlib
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# built in
from datetime import datetime, timedelta
import requests
import json
import itertools
import os


"""
===============================================
User only needs to fill out this section
===============================================
"""

urls = {
'https://api.github.com/repos/ansible/awx/tags': dict(color="red", label="awx"),
'https://api.github.com/repos/ansible/ansible-runner/tags': dict(color="green",  label="runner"),
}
# github > settings > developer settings > personal access token
# export TAGPLOTPAT=personalaccesstoken
github_personal_access_token = os.environ['TAGPLOTPAT']

# only show data from the last N years
cutoff_years = 1

title = "Tag dates"

# save graph as png (empty means no save)
png_path = ""


dpi = 100 # dots per square inch
figsize = (12,6) # 10 inch by 6 inch

"""
===============================================
Gather
===============================================
"""

cutoff = timedelta(days=int(365*cutoff_years))
visdata = []
# make requests to the github api endpoints
for url in urls:
    r = requests.get(url, headers=dict(Authorization=f"token {github_personal_access_token}"), verify=False)
    data = json.loads(r.content.decode())

    # each item in data is a tag. this will get the commit date for this tag
    for item in data:
        commit_url = item['commit']['url']
        commit_r = requests.get(commit_url, headers=dict(Authorization=f"token {github_personal_access_token}"), verify=False)
        commit_data = json.loads(commit_r.content.decode())
        datestr = commit_data['commit']['author']['date'].split('T')[0]
        dateobj = datetime.strptime(datestr, "%Y-%m-%d")
        if datetime.now() - dateobj > cutoff:
            break
        visdata.append(dict(name=item['name'], date=dateobj, url=url))


"""
===============================================
Pre-process
===============================================
"""

# each item in visdata is a tag across all repos
# we should sort by date so that we can generate a proper height bar in the
# graph
visdata = sorted(visdata, key=lambda x: x['date'])
heights = itertools.cycle([-5, 5, -3, 3, -1, 1])
for v in visdata:
    v['height'] = next(heights)

# exampe here is what visdata[0] is
# {'name': '17.1.0',
#  'date': datetime.datetime(2021, 3, 10, 0, 0),
#  'url': 'https://api.github.com/repos/ansible/awx/tags',
#  'height': -5}


"""
===============================================
Plot
===============================================
"""

fig, ax = plt.subplots(figsize=figsize, constrained_layout=True, dpi=dpi)
ax.set(title=title)
for r, (u, url) in enumerate(urls.items()):
    dates = [i['date'] for i in visdata if i['url'] == u]
    names = [i['name'] for i in visdata if i['url'] == u]
    height = [i['height'] for i in visdata if i['url'] == u]
    color = url['color']
    label = url['label']

    markerline, stemline, baseline = ax.stem(dates, height,
                                             linefmt='C0-', basefmt="k-",
                                             use_line_collection=True)

    plt.setp(stemline, 'color', color)

    plt.setp(markerline, mec="k", mfc="w", zorder=3)

    # Shift the markers to the baseline by replacing the y-data by zeros.
    markerline.set_ydata([0 for i in dates])

    # label each line with the tag
    for d, h, n in zip(dates, height, names):
        ax.annotate(n, xy=(d, h), xytext=(3,0), textcoords="offset pixels")

    # format xaxis with monthly intervals
    ax.get_xaxis().set_major_locator(mdates.MonthLocator(interval=1))
    ax.get_xaxis().set_major_formatter(mdates.DateFormatter("%b %Y"))
    plt.setp(ax.get_xticklabels(), rotation=30, ha="right")

    # remove y axis and spines
    ax.get_yaxis().set_visible(False)
    for spine in ["left", "top", "right"]:
        ax.spines[spine].set_visible(False)

    ax.margins(y=0.1)

    # add repo labels on upper right hand corner of graph
    ax.text(0,1-0.05*r, label, color=color, transform=ax.transAxes)
    ypos+=ypos

plt.show(block=False)
if png_path:
    plt.savefig(png_path)
