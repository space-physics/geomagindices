from pathlib import Path
from ftplib import FTP
import requests
from urllib.parse import urlparse
from datetime import datetime, date, timedelta
from typing import Union, Tuple
import subprocess
import socket
import requests.exceptions

URLrecent = 'ftp://ftp.swpc.noaa.gov/pub/weekly/RecentIndices.txt'
URL45dayfcast = 'http://services.swpc.noaa.gov/text/45-day-ap-forecast.txt'
URL20yearfcast = 'https://sail.msfc.nasa.gov/solar_report_archives/May2016Rpt.pdf'


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
        url = ''
        fn = (path / URL20yearfcast.split('/')[-1]).with_suffix('.txt')

    return fn, url


def downloadfile(dt: Union[datetime, date], force: bool) -> Path:

    fn, url = selectApfile(dt)

    if not url or (not force and fn.is_file() and fn.stat().st_size) > 0:
        return fn

    print('download', fn, 'from', url)

    p = urlparse(url)

    host = p[1]
    path = '/'.join(p[2].split('/')[:-1])

    if url.startswith('ftp://'):
        try:
            with FTP(host, 'anonymous', 'guest', timeout=10) as F, fn.open('wb') as f:
                F.cwd(path)
                F.retrbinary(f'RETR {fn.name}', f.write)
        except socket.timeout:
            raise ConnectionError(f'Could not download {url}')
    elif url.startswith(('http://', 'https://')):
        try:
            with fn.open('wb') as f:
                f.write(requests.get(url, allow_redirects=True, timeout=10).content)
        except requests.exceptions.ConnectionError:
            raise ConnectionError(f'Could not download {url}')
    else:
        raise ValueError(f'unsure how to download {url}')

    if fn.suffix == '.pdf' and not fn.with_suffix('.txt').is_file():
        pdf2text(fn)

    return fn


def pdf2text(fn: Path):
    """ for May2016Rpt.pdf """
    subprocess.check_call(['pdftotext', '-layout', '-f', '12', '-l', '15',
                           str(fn)])
