# -*- coding: utf-8 -*-

from typing import List

import xarray as xr
from toolz import curry

from . import processing


@curry
def correlation_calculation(
    data: xr.DataArray,
    bounds: List[int],
    refs: xr.DataArray,
    lag: int,
) -> xr.DataArray:
    """Calculate correlation and return xr.DataArray with Lag value as dimension."""
    return (
        xr.corr(  # type: ignore
            data.isel(time=slice(*bounds)),
            refs.isel(time=slice(bounds[0] - lag, bounds[1] - lag)),
            dim="time",
        )
        .expand_dims("lag")
        .assign_coords({"lag": [lag]})
    )


def main(test: bool = True, lag: int = 24) -> None:
    """Calculate lagged cross correlation."""
    data_path = processing.output_directory(test=test)
    lags = [30 * n for n in range(3 if test else lag)]

    data = xr.open_dataarray(  # type: ignore
        data_path.joinpath("sss-processed.nc"),
    )
    refs = xr.open_dataarray(  # type: ignore
        data_path.joinpath("sss_time_series_processed.nc"),
    )

    curried_correlation_calculation = correlation_calculation(
        data,
        [lags[-1], len(refs)],
        refs,
    )

    data = xr.Dataset(
        {
            "R": (
                ["lag", "latitude", "longitude"],
                xr.concat(
                    [curried_correlation_calculation(lag) for lag in lags],
                    dim="lag",
                ),
            ),
        },
        coords={
            "longitude": (["longitude"], data.coords["longitude"]),
            "latitude": (["latitude"], data.coords["latitude"]),
            "lag": (["lag"], lags),
        },
    )

    return data
