import xarray as xr


def roll(ds: xr.Dataset, dim="longitude") -> xr.Dataset:
    """Rolls data to -180:180 longitude format."""
    ds_east = ds.sel(**{dim: slice(180, 360)})
    ds_east = ds_east.assign_coords({dim: (ds_east[dim] - 360)})
    ds_west = ds.sel(**{dim: slice(0, 180)})
    ds = xr.concat([ds_east, ds_west], dim=dim)
    return ds
