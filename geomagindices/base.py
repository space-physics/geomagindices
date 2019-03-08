import xarray
from typing import Union, List
import numpy as np
from dateutil.parser import parse
from datetime import datetime, date, timedelta

from .web import downloadfile
from .io import load


def getApF107(time: Union[str, datetime, date],
              smoothdays: int = None,
              forcedownload: bool = False) -> xarray.Dataset:
    """
    alternative going back to 1931:
    ftp://ftp.ngdc.noaa.gov/STP/GEOMAGNETIC_DATA/INDICES/KP_AP/

    20 year Forecast data from:
    https://sail.msfc.nasa.gov/solar_report_archives/May2016Rpt.pdf
    """
    dt = todate(time)

    if not isinstance(dt, date) and not isinstance(dt[0], date):
        raise TypeError('must have datetime.date input')

    if isinstance(dt, (list, tuple, np.ndarray)):
        Tind = xarray.Dataset({'f107': None, 'f107s': None, 'Ap': None, 'Aps': None}, coords={'time': None})
        for d in dt:
            Tind = xarray.concat((Tind, getApF107(d, smoothdays, forcedownload)), dim='time')
        return Tind.dropna(dim='time', how='all')

    fn = downloadfile(dt, forcedownload)
# %% load data
    dat = load(fn)
# %% optional smoothing over days
    if isinstance(smoothdays, int):
        periods = np.rint(timedelta(days=smoothdays) / (dat.time[1].item() - dat.time[0].item())).astype(int)
        dat['f107s'] = ('time', moving_average(dat['f107'], periods))
        dat['Aps'] = ('time', moving_average(dat['Ap'], periods))
# %% pull out the time we want
    Indices = dat.sel(time=dt, method='nearest')

    return Indices


def moving_average(dat, periods: int):
    if periods > dat.size:
        raise ValueError('cannot smooth over more time periods than exist in the data')

    return np.convolve(dat,
                       np.ones(periods) / periods,
                       mode='same')


def todate(time: Union[str, date, datetime, np.datetime64]) -> Union[date, List[date]]:

    if isinstance(time, str):
        d = todate(parse(time))
    elif isinstance(time, datetime):
        d = time.date()
    elif isinstance(time, np.datetime64):
        d = time.astype(date)
        if isinstance(d, datetime):
            d = d.date()
    elif isinstance(time, date):
        d = time
    elif isinstance(time, (tuple, list, np.ndarray)):
        d = list(map(todate, time))  # type: ignore
    else:
        raise TypeError(f'{time} must be representable as datetime.date')

    return d
