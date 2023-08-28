from __future__ import annotations
from pathlib import Path
import pandas
import numpy as np
import datetime
from dateutil.parser import parse

from .web import URLmonthly, URL45dayfcast, URL20yearfcast


def load(flist: Path | list[Path]) -> pandas.DataFrame:
    """
    select data to load and collect into pandas.Dataframe by time
    """

    if isinstance(flist, Path):
        flist = [flist]

    monthly_data = pandas.DataFrame(columns=["Ap", "f107"])
    inds = []
    for fn in flist:
        if len(fn.name) == 4:
            inds.append(readdaily(fn))
        elif fn.name == URLmonthly["f107"].split("/")[-1]:
            monthly_data["f107"] = read_monthly(fn)
        elif fn.name == URLmonthly["Ap"].split("/")[-1]:
            monthly_data["Ap"] = read_monthly(fn)
        elif fn.name == URL45dayfcast.split("/")[-1]:
            inds.append(read45dayfcast(fn))
        elif fn.name == URL20yearfcast.split("/")[-1].split(".")[0] + ".txt":
            inds.append(read20yearfcast(fn))
        else:
            raise OSError(fn)

    if monthly_data.size > 0:
        inds.append(monthly_data)

    dat = pandas.concat(inds, sort=True).sort_index()  # destroys metadata

    return dat


# not lru_cache b/c list[path]


def readdaily(flist: Path | list[Path]) -> pandas.DataFrame:
    kp_cols = [
        (12, 14),
        (14, 16),
        (16, 18),
        (18, 20),
        (20, 22),
        (22, 24),
        (24, 26),
        (26, 28),
    ]
    ap_cols = [
        (31, 34),
        (34, 37),
        (37, 40),
        (40, 43),
        (43, 46),
        (46, 49),
        (49, 52),
        (52, 55),
    ]
    f107_cols = (65, 70)

    rawAp: list[str] = []
    rawKp: list[str] = []
    rawf107: list[str] = []
    days = []

    if isinstance(flist, Path):
        flist = [flist]

    for fn in flist:
        with fn.open() as f:
            for line in f:
                # FIXME: century ambiguity of original data
                year = (
                    2000 + int(line[:2]) if int(line[:2]) < 38 else 1900 + int(line[:2])
                )
                days.append(
                    datetime.datetime(year=year, month=int(line[2:4]), day=int(line[4:6]))
                )
                rawAp += [line[i[0] : i[1]] for i in ap_cols]
                rawKp += [line[i[0] : i[1]] for i in kp_cols]

                # f10.7 is daily index
                # MUCH faster to generate here than to fill after DF generation
                rawf107 += [line[f107_cols[0] : f107_cols[1]]] * 8
    # %% construct time
    dtime = [
        day + datetime.timedelta(minutes=m)
        for day in days
        for m in range(90, 24 * 60 + 90, 3 * 60)
    ]
    # %% build and fill array
    names = ["Ap", "Kp"]
    df = pandas.DataFrame(index=dtime, columns=names)
    # tolerate missing values
    df["Ap"] = pandas.to_numeric(rawAp, errors="coerce")

    # Kp / 10 as per ftp://ftp.ngdc.noaa.gov/STP/GEOMAGNETIC_DATA/INDICES/KP_AP/kp_ap.fmt
    # (github issue #2)
    df["Kp"] = pandas.to_numeric(rawKp, errors="coerce") / 10.0
    df["f107"] = pandas.to_numeric(rawf107, errors="coerce")

    df["resolution"] = "d"

    return df


def read20yearfcast(fn: Path) -> pandas.DataFrame:
    """
    uses 50th percentile of Ap and f10.7
    """
    dat = np.loadtxt(fn, usecols=(0, 3, 6), skiprows=11)

    # first column is decimal year, convert to datetime
    year = np.floor(dat[:, 0]).astype(int)
    time = []
    for i in range(year.size):
        boy = datetime.datetime(year[i], 1, 1)
        eoy = datetime.datetime(year[i] + 1, 1, 1)

        seconds = (dat[i, 0] - year[i]) * (eoy - boy).total_seconds()
        time.append(
            datetime.datetime(year[i], 1, 1) + datetime.timedelta(seconds=seconds)
        )

    data = pandas.DataFrame(data=dat[:, 1:3], index=time, columns=["Ap", "f107"])

    data["resolution"] = "m"

    return data


def read_monthly(file: Path) -> pandas.Series:
    if file.suffix == ".json":
        dat = pandas.read_json(file)

        date = [datetime.datetime(int(ym[:4]), int(ym[5:7]), 1) for ym in dat["time-tag"]]
        data = pandas.Series(index=date, data=dat["f10.7"].values)
    elif file.suffix == ".ave":
        dat = np.genfromtxt(file, usecols=range(1, 14), missing_values=".")

        date = []
        for year in dat[:, 0]:
            for month in range(1, 13):
                date.append(datetime.datetime(int(year), month, 1))

        data = pandas.Series(index=date, data=dat[:, 1:].ravel())

    data[data < 0] = np.nan  # by NOAA definition

    return data


def read45dayfcast(fn: Path) -> pandas.DataFrame:
    Ap: list[int] = []

    with fn.open("r") as f:
        for line in f:
            if line[0] in ("#", ":") or line.startswith("45-DAY AP FORECAST"):
                continue
            elif line.startswith("45-DAY F10.7 CM FLUX FORECAST"):
                break
            # %% Ap
            ls = line.split()
            # time += [parse(t) for t in ls[::2]]  # duplicate of below
            Ap += [int(a) for a in ls[1::2]]
        # %% F10.7
        time: list[datetime.datetime] = []
        f107: list[float] = []
        for line in f:
            if line.startswith("FORECASTER"):
                break

            ls = line.split()
            time += [parse(t) for t in ls[::2]]
            f107 += [float(a) for a in ls[1::2]]

    dat = pandas.DataFrame(
        data=np.column_stack((Ap, f107)), index=time, columns=["Ap", "f107"]
    )

    dat["resolution"] = "w"

    return dat
