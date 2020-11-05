# -*- coding: utf-8 -*-

from datetime import timedelta
from pathlib import Path
from typing import Optional

import intake
import pandas as pd
import xarray as xr
from functools import partial
from cftime import DatetimeNoLeap
from statsmodels import api as sm


def open_sss(
    catalog: str = "copernicus-reanalysis.yml",
    source: str = "daily_mean",
) -> xr.Dataset:
    """Open dataset using Intake."""
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
    da: xr.DataArray,
    averaging_method="median",
    quantile: Optional[float] = None,
    longitude: Optional[slice] = None,
    latitude: Optional[slice] = None,
) -> xr.DataArray:
    """Extract the reference time series."""
    if longitude is None:
        longitude = slice(-1, 2)
    if latitude is None:
        latitude = slice(57.5, 59.5)

    return getattr(da.sel(longitude=longitude, latitude=latitude), averaging_method)(
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
        """Init."""
        self.lags = [30 * n for n in range(lag)]
        self.source = source
        self.averaging_method = averaging_method
        self.test = test
        self.clim_method = clim_method
        self.quantile = quantile


def find_trend(da: xr.DataArray, meta_data):
    """Find trend."""
    data = da.values
    shape = data.shape
    result = getattr(
        pd.DataFrame(data.reshape(shape[0], -1)).dropna(axis=1),
        meta_data.averaging_method,
    )(meta_data.quantile, axis=1)
    index = result.index

    model = sm.OLS(result, sm.add_constant(index))
    fit = model.fit()

    trend = fit.params.x1 * index + fit.params.const

    return trend, model, fit


class Climatology(object):
    """Container for climatology calculation approaches."""

    @staticmethod
    def domain_wide(dda_grouped: xr.DataArray, meta_data: MetaData) -> xr.DataArray:
        """Calculate climatology for whole domain."""
        return getattr(dda_grouped, meta_data.averaging_method)(
            meta_data.quantile,
            dim=["longitude", "latitude"],
        )

    @staticmethod
    def point_wise(dda_grouped: xr.DataArray, meta_data: MetaData) -> xr.DataArray:
        """Calculate climatology for each horizontal point."""
        return getattr(dda_grouped, meta_data.averaging_method)(
            meta_data.quantile,
        )


def rm_leap(data: xr.DataArray) -> xr.DataArray:
    """Remove lear days and replace time axis with cftime.DatetimeNoLeap."""
    february = 2
    leap_day = 29
    data = data.sel(
        time=~((data.time.dt.month == february) & (data.time.dt.day == leap_day)),
    )
    data["time"] = [
        DatetimeNoLeap(*data.time[0].values.tolist().timetuple()) + timedelta(d)
        for d, _ in enumerate(data.time)
    ]

    return data


def main(
    averaging_method: str = "quantile",
    quantile: float = 0.9,
    clim_method: str = "domain_wide",
    test: bool = True,
) -> None:
    """Load, detrend and declimatize SSS data."""
    if test:
        output_path = Path.home().joinpath("data", "output", "water-masses", "test")
        meta_data_partial = partial(MetaData, 3)
    else:
        output_path = Path.home().joinpath("data", "output", "water-masses")
        meta_data_partial = partial(MetaData, 24)
    output_path.mkdir(parents=True, exist_ok=True)
    meta_data = meta_data_partial(
        "daily_mean",
        clim_method=clim_method,
        averaging_method=averaging_method,
        test=test,
        quantile=quantile,
    )

    # FIXME: xarray type annotation slug missing
    data = open_sss(source=meta_data.source)["salinity"]
    if test:
        data = data.sel(time=slice("1996-01-01", "1997-12-31")).isel(  # type: ignore
            longitude=slice(None, None, 10),
            latitude=slice(None, None, 10),
        )
    data = rm_leap(data)
    data -= xr.DataArray(find_trend(data, meta_data)[0], [("time", data.time.values)])
    data -= getattr(Climatology, meta_data.clim_method)(
        data.groupby("time.dayofyear"),
        meta_data,
    )

    refser = ref_series(data, meta_data.averaging_method, quantile=meta_data.quantile)

    data = data.to_dataset(name="SSS")  # type: ignore
    data.to_netcdf(output_path.joinpath("sss-processed.nc"))
    refser.to_netcdf(output_path.joinpath("sss_time_series_processed.nc"))


if __name__ == "__main__":
    main(test=True)
