from __future__ import annotations
from pathlib import Path
import ftplib
import requests
from urllib.parse import urlparse
from datetime import datetime, timedelta
import subprocess
import socket
import requests.exceptions
import numpy as np
import importlib.resources

URLmonthly = {
    "f107": "https://services.swpc.noaa.gov/json/solar-cycle/observed-solar-cycle-indices.json",
    "Ap": "ftp://ftp.gfz-potsdam.de/pub/home/obs/kp-ap/ap_monyr.ave",
}
URLdaily = "ftp://ftp.ngdc.noaa.gov/STP/GEOMAGNETIC_DATA/INDICES/KP_AP/"
URL45dayfcast = "https://services.swpc.noaa.gov/text/45-day-ap-forecast.txt"
URL20yearfcast = "https://sail.msfc.nasa.gov/solar_report_archives/May2016Rpt.pdf"

URLNewSource = 'ftp://ftp.gfz-potsdam.de/pub/home/obs/Kp_ap_Ap_SN_F107/'

TIMEOUT = 15  # seconds


def downloadfile(time: np.ndarray, smoothdays: int, force: bool, newsource: bool) -> list[Path]:

    with importlib.resources.path(__package__, "__init__.py") as fn:
        path = fn.parent / "data"
        if not path.is_dir():
            raise NotADirectoryError(path)

    time = np.asarray(time)
    if smoothdays > 0:
        t0 = time[0] - timedelta(smoothdays)
        time = np.concatenate(([t0], time))  # used to handle year edge correctly when smoothdays is supplied
    tnow = datetime.today()
    nearfuture = tnow + timedelta(days=45)

    flist = []
    for t in time:
        if t.timestamp() < tnow.timestamp():  # past
            if not newsource:
                url = f"{URLdaily}{t.year}"
                fn = path / f"{t.year}"
            else:
                url = f"{URLNewSource}/Kp_ap_Ap_SN_F107_{t.year}.txt"
                fn = path / f"Kp_ap_Ap_SN_F107_{t.year}.txt"
            if force or not exist_ok(fn):
                try:
                    download(url, fn)
                    flist.append(fn)
                except ConnectionError:
                    if not newsource:  # backup, lower resolution
                        for url in URLmonthly.values():
                            fn = path / url.split("/")[-1]
                            flist.append(fn)
                            if not exist_ok(fn, timedelta(days=30)):
                                download(url, fn)
                    else:  # no backup for newsource
                        raise ConnectionError
            else:
                flist.append(fn)

        elif (tnow.timestamp() <= t.timestamp()) & (t.timestamp() < nearfuture.timestamp()):  # near future
            fn = path / URL45dayfcast.split("/")[-1]
            if force or not exist_ok(fn, timedelta(days=1)):
                download(URL45dayfcast, fn)

            flist.append(fn)
        elif t.timestamp() > nearfuture.timestamp():  # future
            flist.append((path / URL20yearfcast.split("/")[-1]).with_suffix(".txt"))
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
        with ftplib.FTP(host, "anonymous", "guest", timeout=TIMEOUT) as F, fn.open("wb") as f:
            F.cwd(path)
            F.retrbinary(f"RETR {fn.name}", f.write)
    except (socket.timeout, ftplib.error_perm, socket.gaierror):
        if fn.is_file():  # error while downloading
            fn.unlink()
        raise ConnectionError(f"Could not download {url} to {fn}")


def exist_ok(fn: Path, maxage: timedelta = None) -> bool:
    if not fn.is_file():
        return False

    ok = True
    finf = fn.stat()
    ok &= finf.st_size > 1000
    if maxage is not None:
        ok &= datetime.now() - datetime.utcfromtimestamp(finf.st_mtime) <= maxage

    return ok


def pdf2text(fn: Path):
    """ for May2016Rpt.pdf """
    subprocess.check_call(["pdftotext", "-layout", "-f", "12", "-l", "15", str(fn)])
