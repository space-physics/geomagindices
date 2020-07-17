import datetime


def yeardec2datetime(atime: float) -> datetime.datetime:
    """
    Convert decimal year to datetime.datetime
    http://stackoverflow.com/questions/19305991/convert-fractional-years-to-a-real-date-in-python

    Parameters
    ----------

    atime: float or int
        time in yyyy.fracyear

    Results
    -------
    T: datetime.datetime
        time converted

    """
    if isinstance(atime, (float, int)):  # typically a float
        year = int(atime)
        remainder = atime - year
        boy = datetime.datetime(year, 1, 1)
        eoy = datetime.datetime(year + 1, 1, 1)
        seconds = remainder * (eoy - boy).total_seconds()

        T = boy + datetime.timedelta(seconds=seconds)

    elif isinstance(atime[0], float):
        return [yeardec2datetime(t) for t in atime]
    else:
        raise TypeError(type(atime))

    return T
