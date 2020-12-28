# -*- coding: utf-8 -*-

from datetime import timedelta
from pathlib import Path
from typing import Optional

import intake
import numpy as np
import pandas as pd
import xarray as xr
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
        .chunk({"time": -1})
        .rename(rename_dict)
    )

    return sal.sel(depth=0)


class MetaData(object):
    """Some values required here and there."""

    def __init__(
        self,
        source: str,
        clim_method: str = "point_wise",
        averaging_method: str = "mean",
        quantile: Optional[float] = None,
        test: bool = True,
    ) -> None:
        """Init."""
        self.source = source
        self.averaging_method = averaging_method
        self.test = test
        self.clim_method = clim_method
        self.quantile = quantile


def ref_series(
    da: xr.DataArray,
    md: MetaData,
    longitude: Optional[slice] = None,
    latitude: Optional[slice] = None,
) -> xr.DataArray:
    """Extract the reference time series."""
    if longitude is None:
        longitude = slice(-1, 2)
    if latitude is None:
        latitude = slice(57.5, 59.5)

    return Climatology._climatology(
        da.sel(longitude=longitude, latitude=latitude),
        md,
        dim=["longitude", "latitude"],
    )


class RemoveTrend(object):
    """Container class for trend removal functions."""

    def __init__(self, data, meta_data) -> None:
        """Initialize RemoveTrend."""
        self.data = data
        self.averaging_method = meta_data.averaging_method
        self.quantile = meta_data.quantile

    @staticmethod
    def _domain_wide(data: np.ndarray, averaging_method: str, quantile: float):
        """Find trend."""
        shape = data.shape

        data = getattr(
            pd.DataFrame(data.reshape(shape[0], -1)).dropna(axis=1),
            averaging_method,
        )(quantile, axis=1)
        index = data.index

        model = sm.OLS(data, sm.add_constant(index))
        fit = model.fit()

        return fit.params.x1 * index + fit.params.const

    def domain_wide(self):
        """Remove global trend from data."""
        return self.data - xr.DataArray(
            self._domain_wide(self.data.values, self.averaging_method, self.quantile),
            [("time", self.data.time.values)],
        )

    @staticmethod
    def _point_wise(data: xr.DataArray) -> np.ndarray:
        """Remove trend from 1D time series."""
        index = np.arange(len(data)) / len(data)
        model = sm.OLS(np.asarray(data), sm.add_constant(index))
        fit = model.fit()
        trend = fit.params[1] * index + fit.params[0]

        return data - trend

    def point_wise(self):
        """Calculate and remove temporal trends for each point in space."""
        return xr.apply_ufunc(
            self._point_wise,
            self.data,
            input_core_dims=[["time"]],
            output_core_dims=[["time"]],
            dask="parallelized",
            vectorize=True,
        )


class Climatology(object):
    """Container for climatology calculation approaches."""

    @staticmethod
    def _climatology(da: xr.DataArray, md: MetaData, **kwargs) -> xr.DataArray:
        if md.averaging_method == "mean":
            da = getattr(da, md.averaging_method)(**kwargs)
        elif md.averaging_method == "quantile":
            da = getattr(da, md.averaging_method)(
                md.quantile,
                **kwargs,
            )
        else:
            raise NotImplementedError(
                "Only functions mean and quantile are implemented for "
                "climatology calculation.",
            )
        return da

    @classmethod
    def domain_wide(
        cls,
        dda_grouped: xr.DataArray,
        meta_data: MetaData,
    ) -> xr.DataArray:
        """Calculate climatology for whole domain."""
        return cls._climatology(
            dda_grouped,
            meta_data,
            dim=["longitude", "latitude"],
        )

    @classmethod
    def point_wise(cls, dda_grouped: xr.DataArray, meta_data: MetaData) -> xr.DataArray:
        """Calculate climatology for each horizontal point."""
        return cls._climatology(
            dda_grouped,
            meta_data,
            dim="time",
        )


def rm_leap(data: xr.DataArray) -> xr.DataArray:
    """Remove lear days and replace time axis with cftime.DatetimeNoLeap."""
    february = 2
    leap_day = 29
    data = data.sel(
        time=~((data.time.dt.month == february) & (data.time.dt.day == leap_day)),
    )
    days_since_first = np.cumsum(
        np.append(data.time[1:].values - data.time[:-1].values, timedelta(1)),
    )
    data["time"] = [
        DatetimeNoLeap(*data.time[0].values.tolist().timetuple()) + dt
        for dt in days_since_first
    ]

    return data


def output_directory(test: bool = True) -> Path:
    """Provide path to output directory."""
    if test:
        return Path.home().joinpath("data", "output", "water-masses", "test")
    else:
        return Path.home().joinpath("data", "output", "water-masses")


def main(
    averaging_method: str = "quantile",
    quantile: float = 0.9,
    clim_method: str = "point_wise",
    test: bool = True,
) -> None:
    """Load, detrend and declimatize SSS data."""
    source = "daily_mean" if not test else "test_daily_mean"
    output_path = output_directory(test=test)
    output_path.mkdir(parents=True, exist_ok=True)
    meta_data = MetaData(
        source,
        clim_method=clim_method,
        averaging_method=averaging_method,
        test=test,
        quantile=quantile,
    )

    data = open_sss(source=meta_data.source)["salinity"]
    if test:
        data = data.isel(
            longitude=slice(None, None, 10),
            latitude=slice(None, None, 10),
        )
    data = rm_leap(data)
    data = getattr(RemoveTrend(data, meta_data), meta_data.clim_method)()
    data = data.groupby("time.dayofyear")
    data -= getattr(Climatology, meta_data.clim_method)(
        data,
        meta_data,
    )

    refser = ref_series(data, meta_data)

    data.to_dataset(name="SSS").to_netcdf(output_path.joinpath("sss-processed.nc"))
    refser.to_netcdf(output_path.joinpath("sss_time_series_processed.nc"))


if __name__ == "__main__":
    main()
