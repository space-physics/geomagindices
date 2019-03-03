#!/usr/bin/env python
import pytest
from pytest import approx
import geomagindices as gi
import socket
import requests.exceptions
from datetime import date, timedelta


def test_past():
    t = date(2017, 8, 1)
    tstr = '2017-08-01'

    try:
        dat = gi.getApF107(tstr, 81)
    except socket.error as e:
        pytest.skip(f'possible timeout error {e}')

    assert dat.time.item() == t

    assert dat['f107'] == approx(77.9)
    assert dat['f107s'] == approx(82.533333)
    assert dat['Ap'] == approx(12.)
    assert dat['Aps'] == approx(13.333333)


def test_nearfuture():

    t = date.today() + timedelta(days=3)

    try:
        dat = gi.getApF107(t)
    except requests.exceptions.ConnectionError as e:
        pytest.skip(f'possible timeout error {e}')

    assert dat.time.item() == t

    assert 'Ap' in dat
    assert 'f107' in dat


def test_farfuture():

    t = date(2029, 12, 21)

    try:
        dat = gi.getApF107(t, 81)
    except requests.exceptions.ConnectionError as e:
        pytest.skip(f'possible timeout error {e}')

    assert t - timedelta(days=31) <= dat.time.item() <= t + timedelta(days=31)

    assert 'Ap' in dat
    assert 'f107' in dat


if __name__ == '__main__':
    pytest.main(['-x', __file__])
