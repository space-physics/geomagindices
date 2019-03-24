#!/usr/bin/env python
"""
plot graphs of geophysical indices for comparison with other sources

Example
-------
plot all of 2015

python PlotIndices.py 2015-01-01 2016-01-01
"""
from matplotlib.pyplot import show, figure
import pandas
from dateutil.parser import parse
from datetime import timedelta
import geomagindices as gi


if __name__ == '__main__':
    from argparse import ArgumentParser
    p = ArgumentParser()
    p.add_argument('start_stop', help='date or date range of observation yyyy-mm-dd  (START, STOP)', nargs='+')
    a = p.parse_args()

    start = parse(a.start_stop[0])
    if len(a.start_stop) > 1:
        end = parse(a.start_stop[1])
    else:
        end = start + timedelta(days=1)

    dates = pandas.date_range(start, end, freq='3H')

    inds = gi.get_indices(dates)

# %% plot
    fig = figure()
    ax = fig.gca()
    inds.plot(ax=ax)  # , marker='.'
    ax.set_ylabel('index values')
    ax.set_xlabel('time [UTC]')
    ax.grid(True)

    # fig.savefig('2015.png', bbox_inches='tight')

    show()
