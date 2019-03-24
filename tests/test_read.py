#!/usr/bin/env python
import pytest
from pytest import approx
import geomagindices as gi
from datetime import date, timedelta, datetime


def test_past():
    t = date(2017, 8, 1)
    tstr = '2017-08-01'

    try:
        dat = gi.get_indices(tstr, 81)
    except ConnectionError as e:
        pytest.skip(f'possible timeout error {e}')

    assert dat.shape == (1, 4)
    assert dat.index[0] == t

    assert dat['f107'].item() == approx(77.9)
    assert dat['f107s'].item() == approx(82.533333)
    assert dat['Ap'].item() == approx(12.)
    assert dat['Aps'].item() == approx(13.333333)


def test_nearfuture():

    t = date.today() + timedelta(days=3)

    try:
        dat = gi.get_indices(t)
    except ConnectionError as e:
        pytest.skip(f'possible timeout error {e}')

    assert dat.shape == (1, 2)
    assert dat.index[0] == t

    assert 'Ap' in dat
    assert 'f107' in dat


def test_farfuture():

    t = date(2029, 12, 21)

    dat = gi.get_indices(t, 81)

    assert dat.shape == (1, 4)
    assert dat.index[0] == date(2030, 1, 1)

    assert 'Ap' in dat
    assert 'f107' in dat
    assert 'f107s' in dat
    assert 'Aps' in dat


def test_list():

    t = [date(2019, 1, 1), datetime(2019, 1, 2)]

    dat = gi.get_indices(t)

    assert (dat.index == date(2019, 1, 1)).all


if __name__ == '__main__':
    pytest.main(['-x', __file__])
