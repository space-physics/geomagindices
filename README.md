# Geomagnetic Data Indices

Geomagnetic indices downloader and parser, returns Ap, F10.7 (unsmoothed and smoothed) and Kp.

This is derived from [geomagindices](https://pypi.org/project/geomagindices/), and has been modified to:

- Support the new [post-SWPC data sources for all data dating back to 1932](ftp://ftp.gfz-potsdam.de/pub/home/obs/Kp_ap_Ap_SN_F107/).
- Fix a bug where averaging would not cross year boundaries.

It is a drop-in replacement for [geomagindices](https://pypi.org/project/geomagindices/).

Output datatype is
[pandas.DataFrame](http://pandas.pydata.org/pandas-docs/stable/reference/frame.html)
(for multiple times)

internally, uses
[pandas.Index.get_loc](https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.Index.get_loc.html)
to find nearest time to request.

Missing data is returned as `NaN` (Not a Number floating point value).

## Installation
Direct installation:
```sh
$ pip install geomagdata
```

Indirect installation:
```sh
$ git clone https://github.com/sunipkm/geomagdata
$ cd geomagdata
$ pip install .
```

## Examples

use from other programs like

```python
import geomagdata as gi

inds = gi.get_indices(date)
```

where date is Python
[datetime.date, datetime.datetime](https://docs.python.org/3/library/datetime.html), etc.

---

```sh
python Examples/PlotIndices.py 2015-01-01 2016-01-01
```

![2015 Ap F10.7](./tests/2015.png)
