#!/usr/bin/env python3
"""
retrieve common geomagnetic indices by date
"""

from dateutil.parser import parse

from . import get_indices

from argparse import ArgumentParser

p = ArgumentParser()
p.add_argument("date", help="time of observation yyyy-mm-ddTHH:MM:ss")
p.add_argument(
    "-s", "--smoothdays", help="days to smooth observation for f107a", type=int
)
a = p.parse_args()

inds = get_indices(parse(a.date), a.smoothdays)

print(inds)
