from __future__ import annotations
import pandas
import numpy as np
from datetime import timedelta

from .web import downloadfile
from .io import load


def get_indices(
    time, smoothdays: int | None = None, forcedownload: bool = False
) -> pandas.DataFrame:
    """
    alternative going back to 1931:
    ftp://ftp.ngdc.noaa.gov/STP/GEOMAGNETIC_DATA/INDICES/KP_AP/

    20 year Forecast data from:
    https://sail.msfc.nasa.gov/solar_report_archives/May2016Rpt.pdf
    """

    fn = downloadfile(time, forcedownload)
    # %% load data
    dat: pandas.DataFrame = load(fn)
    # %% optional smoothing over days
    if isinstance(smoothdays, int):
        periods = np.rint(
            timedelta(days=smoothdays) / (dat.index[1] - dat.index[0])
        ).astype(int)

        if "f107" in dat:
            dat["f107s"] = dat["f107"].rolling(periods, min_periods=1).mean()
        if "Ap" in dat:
            dat["Aps"] = dat["Ap"].rolling(periods, min_periods=1).mean()

    # %% pull out the times we want
    i = dat.index.get_indexer(np.atleast_1d(time), method="nearest")
    Indices = dat.iloc[i, :]

    return Indices


getApF107 = get_indices  # legacy


def moving_average(dat: pandas.Series, periods: int):
    if periods > dat.size:
        raise ValueError("cannot smooth over more time periods than exist in the data")

    return np.convolve(dat, np.ones(periods) / periods, mode="same")
