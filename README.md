# Geomagnetic Indices

[![DOI](https://zenodo.org/badge/173524807.svg)](https://zenodo.org/badge/latestdoi/173524807)
![Actions Status](https://github.com/space-physics/geomagindices/workflows/ci/badge.svg)
[![PyPi version](https://img.shields.io/pypi/pyversions/geomagindices.svg)](https://pypi.python.org/pypi/geomagindices)
[![PyPi Download stats](http://pepy.tech/badge/geomagindices)](http://pepy.tech/project/geomagindices)

Geomagnetic indices downloader and parser, returns Ap, F10.7 (unsmoothed and smoothed) and Kp.
Let us know via GitHub Issue if something is missing.

Output datatype is
[pandas.DataFrame](http://pandas.pydata.org/pandas-docs/stable/reference/frame.html)
(for multiple times)

Missing data is returned as `NaN` (Not a Number floating point value).

## Examples

use from other programs like

```python
import geomagindices as gi

inds = gi.get_indices(datetime)
```

where date is Python
[datetime.datetime](https://docs.python.org/3/library/datetime.html), etc.

---

```sh
python Examples/PlotIndices.py 2015-01-01 2016-01-01
```

![2015 Ap F10.7](./tests/2015.png)

## Notes

We should add readers for the new post-SWPC data sources, from 2018 onward as noted at:
https://www.celestrak.com/SpaceData/SpaceWx-format.php

* [Kp, Ap](ftp://ftp.gfz-potsdam.de/pub/home/obs/kp-ap/wdc/)
* [f10.7](ftp://ftp.geolab.nrcan.gc.ca/data/solar_flux/daily_flux_values/fluxtable.txt)

Let us know via GitHub Issue if you want this new data.
