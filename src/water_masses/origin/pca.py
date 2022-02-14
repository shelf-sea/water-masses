# -*- coding: utf-8 -*-
"""Principle Component Analysis."""

from typing import Tuple

import numpy as np
import xarray as xr
import cf_xarray as cfxr  # noqa
from eofs.xarray import Eof

from .. import time_series  # noqa


def lat_weighted_eof(da: xr.DataArray, nmodes: int = 10) -> Tuple[Eof, xr.DataArray]:
    """Calculate PCs and eof solver."""
    coslat = np.cos(np.deg2rad(da.cf.coords["latitude"].values)).clip(0.0, 1.0)
    wgts = np.sqrt(coslat)[..., np.newaxis]
    solver = Eof(da, weights=wgts)
    eof: xr.DataArray = solver.eofsAsCorrelation(neofs=nmodes)

    return solver, eof
