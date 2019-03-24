import pandas
from typing import Union, List
import numpy as np
from dateutil.parser import parse
from datetime import datetime, date, timedelta
import logging

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
    dt = todate(time)

    if not isinstance(dt, date) and not isinstance(dt[0], date):
        raise TypeError('must have datetime.date input')

    if isinstance(dt, (list, tuple, np.ndarray)):
        Tind = pandas.DataFrame(columns=['Ap', 'Aps',
                                         'f107', 'f107s', 'Ap', 'Aps'],
                                index=dt)
        for d in dt:
            Tind = pandas.concat((Tind, get_indices(d, smoothdays, forcedownload)))

        return Tind.dropna(axis=0, how='all')

    fn = downloadfile(dt, forcedownload)
# %% load data
    dat = load(fn)
# %% optional smoothing over days
    if isinstance(smoothdays, int):
        periods = np.rint(timedelta(days=smoothdays) / (dat.index[1] - dat.index[0])).astype(int)
        dat['f107s'] = moving_average(dat['f107'], periods)
        dat['Aps'] = moving_average(dat['Ap'], periods)
# %% pull out the time we want
    try:
        Indices = dat.loc[dt, :]
    except KeyError:
        logging.info('nearest time used')
        i = dat.index.get_loc(dt, method='nearest')
        Indices = dat.iloc[i, :]

    return Indices


getApF107 = get_indices


def moving_average(dat, periods: int) -> np.ndarray:
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
