#!/usr/bin/env python
import pytest
from pytest import approx
import geomagindices as gi
from datetime import date, timedelta, datetime
import pandas


@pytest.mark.parametrize(
    "dt,hour,f107s,ap,aps,kp", [(date(2017, 5, 1), 1, 78.430, 9, 10.43, 2.3), (datetime(2017, 5, 1, 12), 13, 78.47, 2, 10.241, 0.3)]
)
def test_past(dt, hour, f107s, ap, aps, kp):

    try:
        dat = gi.get_indices(dt, 81)
    except ConnectionError as e:
        pytest.skip(f"possible timeout error {e}")

    assert dat.shape[0] == 1
    if dat["resolution"].iloc[0] == "m":
        assert dat["f107"].iloc[0] == approx(73.5, abs=0.1)
        assert dat["f107s"].iloc[0] == approx(76.4, abs=0.1)
        assert dat["Ap"].iloc[0] == 9
        assert dat["Aps"].iloc[0] == approx(9.66, abs=0.1)
    elif dat["resolution"].iloc[0] == "d":
        assert dat["f107"].iloc[0] == approx(76.4)
        assert dat["f107s"].iloc[0] == approx(f107s, abs=0.1)
        assert dat["Ap"].iloc[0] == ap
        assert dat["Aps"].iloc[0] == approx(aps, abs=0.1)
        assert dat["Kp"].iloc[0] == approx(kp, abs=0.1)
    else:
        raise ValueError(f"unknown resolution {dat.resolution}")


def test_nearfuture():

    t = datetime.today() + timedelta(days=3)

    try:
        dat = gi.get_indices(t)
    except ConnectionError as e:
        pytest.skip(f"possible timeout error {e}")

    assert dat.shape[0] == 1

    if t.hour >= 12:
        assert dat.index[0] == datetime(t.year, t.month, t.day) + timedelta(days=1)
    else:
        assert dat.index[0] == datetime(t.year, t.month, t.day)

    assert "Ap" in dat
    assert "f107" in dat


def test_farfuture():

    t = date(2029, 12, 21)

    dat = gi.get_indices(t, 81)

    assert dat.shape == (1, 5)
    assert dat.index[0] == datetime(2030, 1, 1, 2, 37, 40, 799998)

    assert "Ap" in dat
    assert "f107" in dat
    assert "f107s" in dat
    assert "Aps" in dat


def test_list():

    t = [date(2018, 1, 1), datetime(2018, 1, 2)]

    try:
        dat = gi.get_indices(t)
    except ConnectionError as e:
        pytest.skip(f"possible timeout error {e}")

    assert dat.shape[0] == 2
    assert dat.shape[1] in (3, 4)

    assert (dat.index == [datetime(2018, 1, 1, 1, 30), datetime(2018, 1, 2, 1, 30)]).all


def test_multi_past():
    dates = pandas.date_range(datetime(2017, 12, 31, 23), datetime(2018, 1, 1, 2), freq="3H")

    try:
        dat = gi.get_indices(dates)
    except ConnectionError as e:
        pytest.skip(f"possible timeout error {e}")

    assert (dat.index == [datetime(2017, 1, 1, 22, 30), datetime(2018, 1, 1, 1, 30)]).all


def test_past_and_future():
    dates = [datetime(2017, 1, 1), datetime(2030, 3, 1)]

    try:
        dat = gi.get_indices(dates)
    except ConnectionError as e:
        pytest.skip(f"possible timeout error {e}")

    pasttime = datetime(2017, 1, 1)
    if dat["resolution"][0] == "d":
        pasttime += timedelta(hours=1, minutes=30)

    assert (dat.index == [pasttime, datetime(2030, 3, 2, 22, 55, 11, 999997)]).all()


if __name__ == "__main__":
    pytest.main([__file__])
