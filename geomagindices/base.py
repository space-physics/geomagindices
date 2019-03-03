import xarray
from typing import Union, Tuple, List
import numpy as np
from pathlib import Path
from ftplib import FTP
import requests
from dateutil.parser import parse
from urllib.parse import urlparse
import sciencedates as sd
from datetime import datetime, date, timedelta

URLrecent = 'ftp://ftp.swpc.noaa.gov/pub/weekly/RecentIndices.txt'
URL45dayfcast = 'http://services.swpc.noaa.gov/text/45-day-ap-forecast.txt'
URL20yearfcast = 'https://sail.msfc.nasa.gov/solar_report_archives/May2016Rpt.pdf'


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

    assert isinstance(dt, date) or isinstance(dt[0], date), 'must have datetime.date input'
    if isinstance(dt, (list, tuple, np.ndarray)):
        Tind = xarray.Dataset({'f107': None, 'f107s': None, 'Ap': None, 'Aps': None}, coords={'time': None})
        for d in dt:
            Tind = xarray.concat((Tind, getApF107(d, smoothdays, forcedownload)), dim='time')
        return Tind.dropna(dim='time', how='all')

    fn, url = selectApfile(dt)

    downloadfile(fn, url, forcedownload)
# %%
    fn = Path(fn).expanduser()
    if not fn.is_file():
        raise FileNotFoundError(f'{fn} not found.')

    if fn.name == URLrecent.split('/')[-1]:
        dat = readpast(fn)
    elif fn.name == URL45dayfcast.split('/')[-1]:
        dat = read45dayfcast(fn)
    elif fn.name == URL20yearfcast.split('/')[-1].split('.')[0] + '.txt':
        dat = read20yearfcast(fn)
    else:
        raise FileNotFoundError(f'could not determine if you have or which file to read for {dt}')
# %% optional smoothing over days
    if isinstance(smoothdays, int):
        periods = np.rint(timedelta(days=smoothdays) / (dat.time[1].item() - dat.time[0].item())).astype(int)
        dat['f107s'] = ('time', moving_average(dat['f107'], periods))
        dat['Aps'] = ('time', moving_average(dat['Ap'], periods))
# %% pull out the time we want
    Indices = dat.sel(time=dt, method='nearest')

    return Indices


def downloadfile(fn: Path, url: str, force: bool):

    if not force and fn.is_file() and fn.stat().st_size > 0:
        return

    print('download', fn, 'from', url)

    p = urlparse(url)

    host = p[1]
    path = '/'.join(p[2].split('/')[:-1])

    if url.startswith('ftp://'):
        with FTP(host, 'anonymous', 'guest', timeout=10) as F, fn.open('wb') as f:
            F.cwd(path)
            F.retrbinary(f'RETR {fn.name}', f.write)
    elif url.startswith('http://') or url.startswith('https://'):
        with fn.open('wb') as f:
            f.write(requests.get(url, allow_redirects=True, timeout=10).content)
    else:
        raise ValueError(f'unsure how to download {url}')


def moving_average(dat, periods: int):
    if periods > dat.size:
        raise ValueError('cannot smooth over more time periods than exist in the data')

    return np.convolve(dat,
                       np.ones(periods) / periods,
                       mode='same')


def read20yearfcast(fn: Path) -> xarray.Dataset:
    """
    uses 50th percentile of Ap and f10.7
    """
    dat = np.loadtxt(fn, usecols=(0, 3, 6), skiprows=11)

    time = sd.yeardec2datetime(dat[:, 0])

    date = [t.date() for t in time]

    data = xarray.Dataset({'Ap': ('time', dat[:, 1]),
                           'f107': ('time', dat[:, 2])},
                          coords={'time': date})

    return data


def readpast(fn: Path) -> xarray.Dataset:
    dat = np.loadtxt(fn, comments=('#', ':'), usecols=(0, 1, 7, 8, 9, 10))
    date = [parse(f'{ym[0]:.0f}-{ym[1]:02.0f}-01').date() for ym in dat[:, :2]]

    data = xarray.Dataset({'f107': ('time', dat[:, 2]),
                           'Ap': ('time', dat[:, 4])},
                          coords={'time': date})

    data = data.fillna(-1)  # by defn of NOAA

    return data


def read45dayfcast(fn: Path) -> xarray.Dataset:
    Ap = []
    time = []

    with fn.open('r') as f:
        for line in f:
            if line[0] in ('#', ':') or line.startswith('45-DAY AP FORECAST'):
                continue
            elif line.startswith('45-DAY F10.7 CM FLUX FORECAST'):
                break
# %% Ap
            ls = line.split()
            for t, a in zip(ls[::2], ls[1::2]):
                time.append(parse(t).date())
                Ap.append(int(a))

        dat = xarray.Dataset({'Ap': ('time', Ap)},
                             coords={'time': time})
# %% F10.7
        time = []
        f107 = []
        for line in f:
            if line.startswith('FORECASTER'):
                break

            ls = line.split()
            for t, a in zip(ls[::2], ls[1::2]):
                time.append(parse(t).date())
                f107.append(int(a))

        dat['f107'] = ('time', f107)

    return dat


def selectApfile(time: Union[datetime, date]) -> Tuple[Path, str]:
    path = Path(__file__).parent / 'data'
    path.mkdir(exist_ok=True)

    if isinstance(time, datetime):
        time = time.date()

    tnow = date.today()

    if time < tnow:  # past
        url = URLrecent
        fn = path / url.split('/')[-1]
    elif tnow <= time < tnow + timedelta(days=45):  # near future
        url = URL45dayfcast
        fn = path / url.split('/')[-1]
    else:  # future
        url = URL20yearfcast
        rawfn = path / url.split('/')[-1]
        fn = path / rawfn.with_suffix('.txt')

    return fn, url


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
