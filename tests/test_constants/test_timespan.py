# -*- coding: utf-8 -*-

import pytest
from water_masses.constants import Timespan
from datetime import datetime


@pytest.mark.parametrize(
    ("start", "end", "expected"),
    [
        (
            "1993-01-01T00:00:00",
            "2003-01-11T00:01:00",
            {
                "start": datetime.strptime("1993-01-01T00:00:00", "%Y-%m-%dT%H:%M:%S"),
                "end": datetime.strptime("2003-01-11T00:01:00", "%Y-%m-%dT%H:%M:%S"),
            },
        )
    ],
)
def test_Timespan(start, end, expected):
    """Example test with parametrization."""
    assert Timespan(start, end).start == expected["start"]
    assert Timespan(start, end).end == expected["end"]
