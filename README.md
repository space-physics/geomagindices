[![Build Status](https://travis-ci.com/scivision/geomag-indices.svg?branch=master)](https://travis-ci.com/scivision/geomag-indices)
[![Coverage Status](https://coveralls.io/repos/github/scivision/geomag-indices/badge.svg?branch=master)](https://coveralls.io/github/scivision/geomag-indices?branch=master)
[![PyPi version](https://img.shields.io/pypi/pyversions/geomagindices.svg)](https://pypi.python.org/pypi/geomagindices)
[![PyPi Download stats](http://pepy.tech/badge/geomagindices)](http://pepy.tech/project/geomagindices)


# Geomagnetic Indices
Geomagnetic indices downloader and parser, returns Ap, F10.7 (unsmoothed and smoothed).

Output datatype is:

* [pandas.Series](http://pandas.pydata.org/pandas-docs/stable/reference/series.html)  (for single datetime)
* [pandas.DataFrame](http://pandas.pydata.org/pandas-docs/stable/reference/frame.html) (for multiple times)

internally, uses 
[pandas.Index.get_loc](https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.Index.get_loc.html)
to find nearest time to request.

use from other programs like
```python
import geomagindices as gi

inds = gi.get_indices(date)
```

where date is Python 
[datetime.date, datetime.datetime](https://docs.python.org/3/library/datetime.html), etc.
