from __future__ import annotations
from pathlib import Path
import ftplib
import requests
from urllib.parse import urlparse
import datetime
import subprocess
import socket
import requests.exceptions
import numpy as np
import importlib.resources as pkgr
from . import data as fdata

URLmonthly = {
    "f107": "https://services.swpc.noaa.gov/json/solar-cycle/observed-solar-cycle-indices.json",
    "Ap": "ftp://ftp.gfz-potsdam.de/pub/home/obs/kp-ap/ap_monyr.ave",
}
URLdaily = "ftp://ftp.ngdc.noaa.gov/STP/GEOMAGNETIC_DATA/INDICES/KP_AP/"
URL45dayfcast = "https://services.swpc.noaa.gov/text/45-day-ap-forecast.txt"
URL20yearfcast = "https://sail.msfc.nasa.gov/solar_report_archives/May2016Rpt.pdf"
TIMEOUT = 15  # seconds


def downloadfile(time, force: bool) -> list[Path]:
    with pkgr.as_file(pkgr.files(fdata)) as data_path:
        if not data_path.is_dir():
            raise NotADirectoryError(data_path)

    time = np.ravel(time)
    if isinstance(time[0], np.datetime64):
        time = time.astype("datetime64[us]").astype(datetime.datetime)

    tnow = datetime.datetime.today()
    nearfuture = tnow + datetime.timedelta(days=45)

    flist = []
    for t in time:
        if t < tnow:  # past
            url = f"{URLdaily}{t.year}"
            fn = data_path / f"{t.year}"
            if force or not exist_ok(fn):
                try:
                    download(url, fn)
                    flist.append(fn)
                except ConnectionError:  # backup, lower resolution
                    for url in URLmonthly.values():
                        fn = data_path / url.split("/")[-1]
                        flist.append(fn)
                        if not exist_ok(fn, datetime.timedelta(days=30)):
                            download(url, fn)
            else:
                flist.append(fn)

        elif (tnow <= t) & (t < nearfuture):  # near future
            fn = data_path / URL45dayfcast.split("/")[-1]
            if force or not exist_ok(fn, datetime.timedelta(days=1)):
                download(URL45dayfcast, fn)

            flist.append(fn)
        elif t > nearfuture:  # future
            flist.append((data_path / URL20yearfcast.split("/")[-1]).with_suffix(".txt"))
        else:
            raise ValueError(f"Raise a GitHub issue if this is a problem  {t}")

    return list(set(flist))  # dedupe


def download(url: str, fn: Path):
    if url.startswith("http"):
        http_download(url, fn)
    elif url.startswith("ftp"):
        ftp_download(url, fn)
    else:
        raise ValueError(f"not sure how to download {url}")


def http_download(url: str, fn: Path):
    if not fn.parent.is_dir():
        raise NotADirectoryError(fn.parent)

    try:
        R = requests.get(url, allow_redirects=True, timeout=TIMEOUT)
        if R.status_code == 200:
            fn.write_text(R.text)
        else:
            raise ConnectionError(f"Could not download {url} to {fn}")
    except requests.exceptions.ConnectionError:
        raise ConnectionError(f"Could not download {url} to {fn}")


def ftp_download(url: str, fn: Path):
    p = urlparse(url)

    host = p[1]
    path = "/".join(p[2].split("/")[:-1])

    if not fn.parent.is_dir():
        raise NotADirectoryError(fn.parent)

    try:
        with ftplib.FTP(host, "anonymous", "guest", timeout=TIMEOUT) as F, fn.open(
            "wb"
        ) as f:
            F.cwd(path)
            F.retrbinary(f"RETR {fn.name}", f.write)
    except (socket.timeout, ftplib.error_perm, socket.gaierror):
        if fn.is_file():  # error while downloading
            fn.unlink()
        raise ConnectionError(f"Could not download {url} to {fn}")


def exist_ok(fn: Path, maxage: datetime.timedelta | None = None) -> bool:
    if not fn.is_file():
        return False

    ok = True
    finf = fn.stat()
    ok &= finf.st_size > 1000
    if maxage is not None:
        ok &= (
            datetime.datetime.now() - datetime.datetime.utcfromtimestamp(finf.st_mtime)
            <= maxage
        )

    return ok


def pdf2text(fn: Path):
    """for May2016Rpt.pdf"""
    subprocess.check_call(["pdftotext", "-layout", "-f", "12", "-l", "15", str(fn)])
