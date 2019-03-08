[![Build Status](https://travis-ci.com/scivision/geomag-indices.svg?branch=master)](https://travis-ci.com/scivision/geomag-indices)
[![Coverage Status](https://coveralls.io/repos/github/scivision/geomag-indices/badge.svg?branch=master)](https://coveralls.io/github/scivision/geomag-indices?branch=master)
[![PyPi version](https://img.shields.io/pypi/pyversions/geomagindices.svg)](https://pypi.python.org/pypi/geomagindices)
[![PyPi Download stats](http://pepy.tech/badge/geomagindices)](http://pepy.tech/project/geomagindices)


# Geomagnetic Indices
Geomagnetic indices downloader and parser

use from other programs like
```python
import geomagindices as gi

inds = gi.getApF107(date)
```

where date is datetime.date, datetime.datetime, etc.
