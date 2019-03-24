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

URLmonthly = 'ftp://ftp.swpc.noaa.gov/pub/weekly/RecentIndices.txt'
URLdaily = 'ftp://ftp.ngdc.noaa.gov/STP/GEOMAGNETIC_DATA/INDICES/KP_AP/'
URL45dayfcast = 'http://services.swpc.noaa.gov/text/45-day-ap-forecast.txt'
URL20yearfcast = 'https://sail.msfc.nasa.gov/solar_report_archives/May2016Rpt.pdf'


def downloadfile(time: np.ndarray, force: bool) -> List[Path]:
    path = Path(__file__).parent / 'data'
    path.mkdir(exist_ok=True)

    time = np.asarray(time)

    tnow = datetime.today()

    nearfuture = tnow + timedelta(days=45)

    flist = []

    for t in time:
        if t < tnow:  # past
            url = f'{URLdaily}{t.year}'
            fn = path / f'{t.year}'
            flist.append(fn)

            if not force and exist_ok(fn):
                continue
            ftp_download(url, fn)
        elif (tnow <= t) & (t < nearfuture):  # near future
            fn = path / URL45dayfcast.split('/')[-1]
            if force or not exist_ok(fn):
                http_download(URL45dayfcast, fn)

            flist.append(fn)
        elif t > nearfuture:  # future
            flist.append((path / URL20yearfcast.split('/')[-1]).with_suffix('.txt'))
        else:
            raise NotImplementedError(
                'make sure all times are before or after current time. Raise a GitHub issue if this is a problem')

    return list(set(flist))  # dedupe


def http_download(url: str, fn: Path):
    try:
        R = requests.get(url, allow_redirects=True, timeout=10)
        if R.status_code == 200:
            fn.write_text(R.text)
        else:
            raise ConnectionError(f'Could not download {url}')
    except requests.exceptions.ConnectionError:
        raise ConnectionError(f'Could not download {url}')


def ftp_download(url: str, fn: Path):

    p = urlparse(url)

    host = p[1]
    path = '/'.join(p[2].split('/')[:-1])

    try:
        with ftplib.FTP(host, 'anonymous', 'guest', timeout=10) as F, fn.open('wb') as f:
            F.cwd(path)
            F.retrbinary(f'RETR {fn.name}', f.write)
    except (socket.timeout, ftplib.error_perm):
        raise ConnectionError(f'Could not download {url}')


def exist_ok(fn: Path) -> bool:
    if fn.is_file():
        finf = fn.stat()
        return finf.st_size > 1000

    return False


def pdf2text(fn: Path):
    """ for May2016Rpt.pdf """
    subprocess.check_call(['pdftotext', '-layout', '-f', '12', '-l', '15',
                           str(fn)])
