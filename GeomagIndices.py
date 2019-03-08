#!/usr/bin/env python
"""
simple demo of retrieving common geomagnetic indices by date
"""
import geomagindices as gi


if __name__ == '__main__':
    from argparse import ArgumentParser
    p = ArgumentParser()
    p.add_argument('date', help='date of observation yyyy-mm-dd')
    a = p.parse_args()

    inds = gi.getApF107(a.date)

    print(f'{inds.time.item()}   Ap: {inds.Ap.item()}  f10.7: {inds.f107.item()}')
