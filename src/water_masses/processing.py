# -*- coding: utf-8 -*-

from datetime import timedelta
from pathlib import Path
from typing import Optional

import intake
import pandas as pd
import xarray as xr
from cftime import DatetimeNoLeap
from matplotlib import pyplot as plt
from statsmodels import api as sm


def open_sss(
    catalog: str = "copernicus-reanalysis.yml", source: str = "daily_mean"
) -> xr.Dataset:
    rename_dict = {"so": "salinity"}
    sal = (
        intake.open_catalog(str(Path(__file__).parent.joinpath("data", catalog)))[
            source
        ]
        .to_dask()
        .rename(rename_dict)
    )

    return sal.sel(depth=0)


def ref_series(
    da: xr.DataArray, averaging_method="median", quantile: Optional[float] = None
) -> xr.DataArray:
    """Extract the reference time series."""
    box = {"longitude": slice(-1, 2), "latitude": slice(57.5, 59.5)}
    return getattr(da.sel(**box), averaging_method)(
        quantile,
        dim=["longitude", "latitude"],
    )


class MetaData(object):
    """Some values required here and there."""

    def __init__(
        self,
        lag: int,
        source: str,
        clim_method: str = "domain_wide",
        averaging_method: str = "mean",
        quantile: Optional[float] = None,
        test: bool = True,
    ) -> None:
        self.lags = [30 * n for n in range(lag)]
        self.source = source
        self.averaging_method = averaging_method
        self.test = test
        self.clim_method = clim_method
        self.quantile = quantile


def find_trend(da: xr.DataArray, meta_data):
    """Find trend."""
    A = da.values
    s = A.shape
    y = getattr(
        pd.DataFrame(A.reshape(s[0], -1)).dropna(axis=1), meta_data.averaging_method
    )(meta_data.quantile, axis=1)
    x = y.index

    model = sm.OLS(y, sm.add_constant(x))
    results = model.fit()

    trend = results.params.x1 * x + results.params.const

    return trend, model, results


class Climatology(object):
    """Container for climatology calculation approaches."""

    @staticmethod
    def domain_wide(dda_grouped: xr.DataArray, meta_data: MetaData) -> xr.DataArray:
        return getattr(dda_grouped, meta_data.averaging_method)(
            meta_data.quantile,
            dim=["longitude", "latitude"],
        )

    @staticmethod
    def point_wise(dda_grouped: xr.DataArray, meta_data: MetaData) -> xr.DataArray:
        return getattr(dda_grouped, meta_data.averaging_method)(
            meta_data.quantile,
        )


def rm_leap(data: xr.DataArray) -> xr.DataArray:
    """Remove lear days and replace time axis with cftime.DatetimeNoLeap."""
    data = data.sel(
        time=~((data.time.dt.month == 2) & (data.time.dt.day == 29)),
    )
    data["time"] = [
        DatetimeNoLeap(*data.time[0].values.tolist().timetuple()) + timedelta(d)
        for d, _ in enumerate(data.time)
    ]

    return data


def main(test: bool = True) -> None:
    """Load, detrend and declimatize SSS data."""
    AVERAGING_METHOD = "quantile"
    QUANTILE = 0.9
    CLIM_METHOD = "domain_wide"
    output_path = Path.home().joinpath("data", "output", "water-masses")
    output_path.mkdir(parents=True, exist_ok=True)

    if test:
        meta_data = MetaData(
            3,
            "test_daily_mean",
            clim_method=CLIM_METHOD,
            averaging_method=AVERAGING_METHOD,
            test=test,
            quantile=QUANTILE,
        )
    else:
        meta_data = MetaData(
            24,
            "daily_mean",
            clim_method=CLIM_METHOD,
            averaging_method=AVERAGING_METHOD,
            test=test,
            quantile=QUANTILE,
        )

    data = open_sss(source=meta_data.source)
    data = rm_leap(data.salinity)
    data -= xr.DataArray(find_trend(data, meta_data)[0], [("time", data.time.values)])
    data -= getattr(Climatology, meta_data.clim_method)(
        data.groupby("time.dayofyear"), meta_data
    )

    refser = ref_series(data, meta_data.averaging_method, quantile=meta_data.quantile)

    data = data.to_dataset(name="SSS")

    data.to_netcdf(output_path.joinpath("sss-processed.nc"))
    refser.to_netcdf(output_path.joinpath("sss_time_series_processed.nc"))


if __name__ == "__main__":
    main(test=True)
