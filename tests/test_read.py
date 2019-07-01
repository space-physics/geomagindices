#!/usr/bin/env python
import pytest
from pytest import approx
import geomagindices as gi
from datetime import date, timedelta, datetime
import pandas


def test_past_date():
    t = date(2017, 8, 1)

    try:
        dat = gi.get_indices(t, 81)
    except ConnectionError as e:
        pytest.skip(f'possible timeout error {e}')

    assert dat.shape[0] == 1
    assert dat.index[0] == datetime(2017, 8, 1, 1, 30)

    assert dat['f107'].item() == approx(75.7)
    assert dat['f107s'].item() == approx(84.611111, abs=0.01)
    assert dat['Ap'].item() == 3
    assert dat['Aps'].item() == approx(10.8888888, abs=0.01)


def test_past_datetime():
    t = datetime(2017, 8, 1, 12)

    try:
        dat = gi.get_indices(t, 81)
    except ConnectionError as e:
        pytest.skip(f'possible timeout error {e}')

    assert dat.shape[0] == 1
    assert dat.index[0] == datetime(2017, 8, 1, 13, 30)

    assert dat['f107'].item() == approx(75.7)
    assert dat['f107s'].item() == approx(84.7679012, abs=0.01)
    assert dat['Ap'].item() == 9
    assert dat['Aps'].item() == approx(10.9135802, abs=0.01)


def test_nearfuture():

    t = datetime.today() + timedelta(days=3)

    try:
        dat = gi.get_indices(t)
    except ConnectionError as e:
        pytest.skip(f'possible timeout error {e}')

    assert dat.shape[0] == 1

    if t.hour >= 12:
        assert dat.index[0] == datetime(t.year, t.month, t.day)+timedelta(days=1)
    else:
        assert dat.index[0] == datetime(t.year, t.month, t.day)

    assert 'Ap' in dat
    assert 'f107' in dat


def test_farfuture():

    t = date(2029, 12, 21)

    dat = gi.get_indices(t, 81)

    assert dat.shape == (1, 4)
    assert dat.index[0] == datetime(2030, 1, 1, 2, 37, 40, 799998)

    assert 'Ap' in dat
    assert 'f107' in dat
    assert 'f107s' in dat
    assert 'Aps' in dat


def test_list():

    t = [date(2018, 1, 1), datetime(2018, 1, 2)]

    try:
        dat = gi.get_indices(t)
    except ConnectionError as e:
        pytest.skip(f'possible timeout error {e}')

    assert (dat.index == [datetime(2018, 1, 1, 1, 30),
                          datetime(2018, 1, 2, 1, 30)]).all


def test_multi_past():
    dates = pandas.date_range(datetime(2017, 12, 31, 23), datetime(2018, 1, 1, 2),
                              freq='3H')

    try:
        dat = gi.get_indices(dates)
    except ConnectionError as e:
        pytest.skip(f'possible timeout error {e}')

    assert (dat.index == [datetime(2017, 1, 1, 22, 30),
                          datetime(2018, 1, 1, 1, 30)]).all


def test_past_and_future():
    dates = [datetime(2017, 1, 1), datetime(2030, 3, 1)]

    try:
        dat = gi.get_indices(dates)
    except ConnectionError as e:
        pytest.skip(f'possible timeout error {e}')

    assert (dat.index == [datetime(2017, 1, 1, 1, 30), datetime(2030, 3, 2, 22, 55, 11, 999997)]).all()


if __name__ == '__main__':
    pytest.main(['-x', __file__])
