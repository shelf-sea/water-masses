# -*- coding: utf-8 -*-
"""Experiment constants."""

from datetime import datetime


class Timespan(object):
    """Container of timespan of the experiment."""

    def __init__(
        self,
        start: str = "1993-01-01T00:00:00",
        end: str = "2019-12-31T00:00:00",
    ) -> None:
        """Start and end of analysis time series.

        Parameter
        =========
        start : str
            start of timeperiod of analysis
        end : str
            end of timeperiod of analysis

        """
        self.start: datetime = datetime.strptime(start, "%Y-%m-%dT%H:%M:%S")
        self.end: datetime = datetime.strptime(end, "%Y-%m-%dT%H:%M:%S")
