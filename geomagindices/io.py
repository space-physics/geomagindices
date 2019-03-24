from pathlib import Path
import pandas
import numpy as np
from datetime import datetime, timedelta
from typing import Sequence, Union, List, Iterable
from dateutil.parser import parse

from .web import URLmonthly, URL45dayfcast, URL20yearfcast
import sciencedates as sd


def load(flist: Union[Path, Sequence[Path]]) -> pandas.DataFrame:

    if isinstance(flist, Path):
        flist = [flist]

    inds = []
    for fn in flist:
        if len(fn.name) == 4:
            inds.append(readdaily(fn))
        elif fn.name == URLmonthly.split('/')[-1]:
            inds.append(readmonthly(fn))
        elif fn.name == URL45dayfcast.split('/')[-1]:
            inds.append(read45dayfcast(fn))
        elif fn.name == URL20yearfcast.split('/')[-1].split('.')[0] + '.txt':
            inds.append(read20yearfcast(fn))
        else:
            raise FileNotFoundError(f'could not determine how to read {fn}')
# %% concat results
    if len(inds) == 1:
        dat = inds[0]
    else:
        dat = pandas.concat(inds, sort=True).sort_index()

    return dat

# not lru_cache b/c list[path]


def readdaily(flist: Union[Path, Iterable[Path]]) -> pandas.DataFrame:
    kp_cols = [(12, 14), (14, 16), (16, 18), (18, 20), (20, 22), (22, 24), (24, 26), (26, 28)]
    ap_cols = [(31, 34), (34, 37), (37, 40), (40, 43), (43, 46), (46, 49), (49, 52), (52, 55)]
    f107_cols = (65, 70)

    rawAp: List[str] = []
    rawKp: List[str] = []
    rawf107: List[str] = []
    days = []

    if isinstance(flist, Path):
        flist = [flist]

    for fn in flist:
        with fn.open() as f:
            for line in f:
                # FIXME: century ambiguity of original data
                year = 2000 + int(line[:2]) if int(line[:2]) < 38 else 1900 + int(line[:2])
                days.append(datetime(year=year,
                                     month=int(line[2:4]),
                                     day=int(line[4:6])))
                rawAp += [line[i[0]:i[1]] for i in ap_cols]
                rawKp += [line[i[0]:i[1]] for i in kp_cols]

                # f10.7 is daily index
                # MUCH faster to generate here than to fill after DF generation
                rawf107 += [line[f107_cols[0]:f107_cols[1]]]*8
# %% construct time
    dtime = [day + timedelta(minutes=m) for day in days for m in range(90, 24*60+90, 3*60)]
# %% build and fill array
    names = ['Ap', 'Kp']
    df = pandas.DataFrame(index=dtime, columns=names)
    # numpy.genfromtxt to tolerate missing values
    df['Ap'] = pandas.to_numeric(rawAp,  errors='coerce')
    df['Kp'] = pandas.to_numeric(rawKp,  errors='coerce')
    df['f107'] = pandas.to_numeric(rawf107,  errors='coerce')

    return df


def read20yearfcast(fn: Path) -> pandas.DataFrame:
    """
    uses 50th percentile of Ap and f10.7
    """
    dat = np.loadtxt(fn, usecols=(0, 3, 6), skiprows=11)

    time = sd.yeardec2datetime(dat[:, 0])

    data = pandas.DataFrame(data=dat[:, 1:3],
                            index=time,
                            columns=['Ap', 'f107'])

    return data


def readmonthly(fn: Path) -> pandas.DataFrame:
    dat = np.loadtxt(fn, comments=('#', ':'), usecols=(0, 1, 7, 8, 9, 10))
    date = [parse(f'{ym[0]:.0f}-{ym[1]:02.0f}-01') for ym in dat[:, :2]]

    data = pandas.DataFrame(np.column_stack((dat[:, 4], dat[:, 2])),
                            index=date,
                            columns=['Ap', 'f107'])

    data = data.fillna(-1)  # by defn of NOAA

    return data


def read45dayfcast(fn: Path) -> pandas.DataFrame:
    Ap: List[int] = []

    with fn.open('r') as f:
        for line in f:
            if line[0] in ('#', ':') or line.startswith('45-DAY AP FORECAST'):
                continue
            elif line.startswith('45-DAY F10.7 CM FLUX FORECAST'):
                break
# %% Ap
            ls = line.split()
            # time += [parse(t) for t in ls[::2]]  # duplicate of below
            Ap += [int(a) for a in ls[1::2]]
# %% F10.7
        time: List[datetime] = []
        f107: List[float] = []
        for line in f:
            if line.startswith('FORECASTER'):
                break

            ls = line.split()
            time += [parse(t) for t in ls[::2]]
            f107 += [float(a) for a in ls[1::2]]

    dat = pandas.DataFrame(data=np.column_stack((Ap, f107)),
                           index=time,
                           columns=['Ap', 'f107'])

    return dat
