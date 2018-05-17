from enum import Enum
from threading import Thread, Event
from datetime import datetime

class Result(Enum):
    PENDING = 0
    ONGOING = 1
    SUSPICIOUS = 2
    NOK = 2
    CANCELLED = 8
    OK = 10

class Sampling(Enum):
    ongoing = 0
    every_unit = 1

    each_10 = 21
    each_100 = 22
    each_1000 = 23
    each_10000 = 24
    each_100000 = 25

    by_second = 30
    by_minute = 31
    by_hour = 32
    by_day = 33
    by_week = 34
    by_month = 35
    by_year = 36
