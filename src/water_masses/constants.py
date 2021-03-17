# -*- coding: utf-8 -*-
"""Experiment constants."""

from datetime import datetime


class Timespan(object):
    start: datetime = datetime.strptime("1993-01-01", "%Y-%m-%d")
    end: datetime = datetime.strptime("2019-12-31", "%Y-%m-%d")
