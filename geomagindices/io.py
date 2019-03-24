from pathlib import Path
import pandas
import numpy as np
from dateutil.parser import parse

from .web import URLrecent, URL45dayfcast, URL20yearfcast
import sciencedates as sd


def load(fn: Path) -> pandas.DataFrame:
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
        raise FileNotFoundError(f'could not determine how to read {fn}')

    return dat


def read20yearfcast(fn: Path) -> pandas.DataFrame:
    """
    uses 50th percentile of Ap and f10.7
    """
    dat = np.loadtxt(fn, usecols=(0, 3, 6), skiprows=11)

    time = sd.yeardec2datetime(dat[:, 0])

    date = [t.date() for t in time]

    data = pandas.DataFrame(data=dat[:, 1:3],
                            index=date,
                            columns=['Ap', 'f107'])

    return data


def readpast(fn: Path) -> pandas.DataFrame:
    dat = np.loadtxt(fn, comments=('#', ':'), usecols=(0, 1, 7, 8, 9, 10))
    date = [parse(f'{ym[0]:.0f}-{ym[1]:02.0f}-01').date() for ym in dat[:, :2]]

    data = pandas.DataFrame(np.column_stack((dat[:, 4], dat[:, 2])),
                            index=date,
                            columns=['Ap', 'f107'])

    data = data.fillna(-1)  # by defn of NOAA

    return data


def read45dayfcast(fn: Path) -> pandas.DataFrame:
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

        dat = pandas.DataFrame(data=np.column_stack((Ap, f107)),
                               index=time,
                               columns=['Ap', 'f107'])

    return dat
