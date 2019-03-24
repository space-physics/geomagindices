import pandas
from typing import Union
import numpy as np
from dateutil.parser import parse
from datetime import datetime, date, timedelta

from .web import downloadfile
from .io import load


def get_indices(time: Union[str, datetime, date],
                smoothdays: int = None,
                forcedownload: bool = False) -> pandas.DataFrame:
    """
    alternative going back to 1931:
    ftp://ftp.ngdc.noaa.gov/STP/GEOMAGNETIC_DATA/INDICES/KP_AP/

    20 year Forecast data from:
    https://sail.msfc.nasa.gov/solar_report_archives/May2016Rpt.pdf
    """
    dtime = todatetime(time)

    fn = downloadfile(dtime, forcedownload)
# %% load data
    dat = load(fn)
# %% optional smoothing over days
    if isinstance(smoothdays, int):
        periods = np.rint(timedelta(days=smoothdays) / (dat.index[1] - dat.index[0])).astype(int)
        dat['f107s'] = moving_average(dat['f107'], periods)
        dat['Aps'] = moving_average(dat['Ap'], periods)
# %% pull out the times we want
    i = [dat.index.get_loc(t, method='nearest') for t in dtime]
    Indices = dat.iloc[i, :]

    return Indices


getApF107 = get_indices  # legacy


def moving_average(dat, periods: int) -> np.ndarray:
    if periods > dat.size:
        raise ValueError('cannot smooth over more time periods than exist in the data')

    return np.convolve(dat,
                       np.ones(periods) / periods,
                       mode='same')


def todatetime(time: Union[str, date, datetime, np.datetime64]) -> np.ndarray:

    if isinstance(time, str):
        d = todatetime(parse(time))
    elif isinstance(time, datetime):
        d = time
    elif isinstance(time, np.datetime64):
        d = time.astype(date)
    elif isinstance(time, date):
        d = datetime(time.year, time.month, time.day)
    elif isinstance(time, (tuple, list, np.ndarray)):
        d = np.atleast_1d([todatetime(t) for t in time]).squeeze()
    elif isinstance(time, pandas.DatetimeIndex):
        d = time.to_pydatetime()
    else:
        raise TypeError(f'{time} must be representable as datetime.date')

    dates = np.atleast_1d(d).ravel()

    return dates


def todate(time: Union[str, date, datetime, np.datetime64]) -> np.ndarray:

    if isinstance(time, str):
        d = todate(parse(time))
    elif isinstance(time, datetime):
        d = time.date()
    elif isinstance(time, np.datetime64):
        d = time.astype(date)
    elif isinstance(time, date):
        d = time
    elif isinstance(time, (tuple, list, np.ndarray)):
        d = np.atleast_1d([todate(t) for t in time]).squeeze()
    else:
        raise TypeError(f'{time} must be representable as datetime.date')

    dates = np.atleast_1d(d).ravel()

    return dates
