from pathlib import Path
import ftplib
import requests
from urllib.parse import urlparse
from datetime import datetime, timedelta
import subprocess
from typing import List
import socket
import requests.exceptions
import numpy as np
import pkg_resources

URLmonthly = 'ftp://ftp.swpc.noaa.gov/pub/weekly/RecentIndices.txt'
URLdaily = 'ftp://ftp.ngdc.noaa.gov/STP/GEOMAGNETIC_DATA/INDICES/KP_AP/'
URL45dayfcast = 'https://services.swpc.noaa.gov/text/45-day-ap-forecast.txt'
URL20yearfcast = 'https://sail.msfc.nasa.gov/solar_report_archives/May2016Rpt.pdf'
TIMEOUT = 15  # seconds


def downloadfile(time: np.ndarray, force: bool) -> List[Path]:
    # path = Path(__file__).parents[1] / 'data'  # doesn't always work from virtualenv e.g. Travis-CI
    path = Path(pkg_resources.resource_filename(__name__, '__init__.py')).parent / 'data'
    if not path.is_dir():
        raise NotADirectoryError(path)

    time = np.asarray(time)
    tnow = datetime.today()
    nearfuture = tnow + timedelta(days=45)

    flist = []
    for t in time:
        if t < tnow:  # past
            url = f'{URLdaily}{t.year}'
            fn = path / f'{t.year}'
            if force or not exist_ok(fn):
                try:
                    ftp_download(url, fn)
                except ConnectionError:  # backup, lower resolution
                    fn = path / URLmonthly.split('/')[-1]
                    if not exist_ok(fn, timedelta(days=30)):
                        ftp_download(URLmonthly, fn)
            flist.append(fn)
        elif (tnow <= t) & (t < nearfuture):  # near future
            fn = path / URL45dayfcast.split('/')[-1]
            if force or not exist_ok(fn, timedelta(days=1)):
                http_download(URL45dayfcast, fn)

            flist.append(fn)
        elif t > nearfuture:  # future
            flist.append((path / URL20yearfcast.split('/')[-1]).with_suffix('.txt'))
        else:
            raise ValueError(f'Raise a GitHub issue if this is a problem  {t}')

    return list(set(flist))  # dedupe


def http_download(url: str, fn: Path):
    if not fn.parent.is_dir():
        raise NotADirectoryError(fn.parent)

    try:
        R = requests.get(url, allow_redirects=True, timeout=TIMEOUT)
        if R.status_code == 200:
            fn.write_text(R.text)
        else:
            raise ConnectionError(f'Could not download {url} to {fn}')
    except requests.exceptions.ConnectionError:
        raise ConnectionError(f'Could not download {url} to {fn}')


def ftp_download(url: str, fn: Path):

    p = urlparse(url)

    host = p[1]
    path = '/'.join(p[2].split('/')[:-1])

    if not fn.parent.is_dir():
        raise NotADirectoryError(fn.parent)

    try:
        with ftplib.FTP(host, 'anonymous', 'guest', timeout=TIMEOUT) as F, fn.open('wb') as f:
            F.cwd(path)
            F.retrbinary(f'RETR {fn.name}', f.write)
    except (socket.timeout, ftplib.error_perm, socket.gaierror):
        if fn.is_file():  # error while downloading
            fn.unlink()
        raise ConnectionError(f'Could not download {url} to {fn}')


def exist_ok(fn: Path,
             maxage: timedelta = None) -> bool:
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
    subprocess.check_call(['pdftotext', '-layout', '-f', '12', '-l', '15',
                           str(fn)])
