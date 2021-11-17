# -*- coding: utf-8 -*-
"""Time series manipulations."""

from typing import Tuple

import pandas as pd
from scipy import signal
import xarray as xr
import numpy as np


def lowpass_filter(
    df: pd.DataFrame,
    var: str,
    order: int = 10,
    freq: float = 12,
    cutoff: float = 4,
) -> pd.DataFrame:
    """Apply low pass filter."""
    nyq = 0.5 * freq
    sos = signal.butter(
        N=order,
        Wn=cutoff / nyq,
        btype="lowpass",
        fs=freq,
        output="sos",
    )
    df[f"f{var}"] = signal.sosfiltfilt(sos, df[var])
    return df


def crosscorr(datax, datay, lag=0):
    """Lag-N cross correlation.
    Parameters
    ----------
    lag : int, default 0
    datax, datay : pandas.Series objects of equal length

    Returns
    ----------
    crosscorr : float

    From
    ----
    https://stackoverflow.com/a/37215839

    """
    return datax.corr(datay.shift(lag))


def detrend(data: xr.DataArray, dim: str, deg: int = 1) -> xr.DataArray:
    """Detrend along a single dimension."""
    p = data.polyfit(dim=dim, deg=deg)
    fit = xr.polyval(data[dim], p.polyfit_coefficients)
    return data - fit


def _cross_year_winter_months(
    da: xr.DataArray, y_n=list
) -> Tuple[xr.DataArray, xr.DataArray]:
    """Calculate a touple of consecutive December, January, and February.

    Assumes time dimension to be the last. e.g. (lon, lat, t)
    """
    return (
        da[..., da.time.dt.year.isin(y_n - 1) & da.time.dt.month.isin([12])],
        da[..., da.time.dt.year.isin(y_n) & da.time.dt.month.isin([1, 2])],
    )


def _winter_mean(da: xr.DataArray, y_n) -> np.ndarray:
    """Average cross year winter months tuple."""
    return np.expand_dims(
        np.mean(
            np.concatenate(_cross_year_winter_months(da, y_n), axis=-1),
            axis=-1,
        ),
        axis=-1,
    )


def cross_year_winter_average(da):
    da_djf = da[..., da.time.dt.season == "DJF"]
    years_complete_djf = list(set(da_djf.time.dt.year.values))[1:]
    da_seasonal_average = xr.DataArray(
        data=np.concatenate(
            [_winter_mean(da_djf, y_n) for y_n in years_complete_djf], axis=-1
        ),
        dims=["lat", "lon", "time"],
        coords=dict(
            lon=(["lon"], da_djf.lon.values),
            lat=(["lat"], da_djf.lat.values),
            time=pd.date_range(
                start=f"{years_complete_djf[0]}",
                end=f"{years_complete_djf[-1]}",
                freq="AS-JAN",
            )
            + pd.Timedelta(14, unit="D"),
        ),
    ).transpose("time", "lat", "lon")
    da_seasonal_average = da_seasonal_average.cf.guess_coord_axis()
    return da_seasonal_average
