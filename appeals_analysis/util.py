import datetime
import functools

_open = functools.partial(open, encoding="utf8")


def parse_date(str_):
    str_ = str_.split("T")[0]
    return datetime.datetime.strptime(str_, "%Y-%m-%d").date()
