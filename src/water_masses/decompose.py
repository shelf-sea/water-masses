# -*- coding: utf-8 -*-
"""Decomposition of data sets."""

import xarray as xr
import pandas as pd
from typing import Tuple


def from_monthly_index(
    datafield: xr.Dataset, filtindex: pd.DataFrame
) -> Tuple[int, xr.Dataset]:
    """Filter daily data based on a monthly index."""
    pain_fucking_ful_shit_manual_list_of_fucking_days_in_fucking_months = [
        day.values
        for day in datafield.time
        if (day.dt.year, day.dt.month)
        in zip(filtindex.date.dt.year, filtindex.date.dt.month)
    ]

    return len(
        pain_fucking_ful_shit_manual_list_of_fucking_days_in_fucking_months
    ), datafield.sel(
        time=pain_fucking_ful_shit_manual_list_of_fucking_days_in_fucking_months
    )
