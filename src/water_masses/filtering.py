from typing import Callable, Dict, List

import cf_xarray as cfxr  # noqa
import numpy as np
import xarray as xr
from scipy import signal


def apply_filter(
    filter_func: Callable[..., np.ndarray],
    data: xr.DataArray,
    filter_args: List[float],
    filter_kwgs: Dict[str, int],
) -> xr.DataArray:
    """Apply filter to xarray DataArray."""
    data = data.copy()
    data.values = xr.apply_ufunc(
        filter_func,
        data,
        *filter_args,
        kwargs=filter_kwgs,
        input_core_dims=[["time"], *[[] for _ in range(len(filter_args))]],
        output_core_dims=[["time"]],
        vectorize=True,
    ).cf.transpose("time", "latitude", "longitude")

    return data


def butter_lowpass_filter(
    data: np.ndarray, cutlen: int = 15, fs: int = 12, order=5
) -> np.ndarray:
    """1D lowpass butterworth filter."""
    return signal.sosfiltfilt(
        signal.butter(
            order, 1 / cutlen / (0.5 * fs), analog=False, btype="lowpass", output="sos"
        ),
        data,
    )
