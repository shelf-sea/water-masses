# -*- coding: utf-8 -*-
"""Create seeding file for Tracmass."""
from pathlib import Path
from typing import Optional, Union, List, Tuple, Dict
import io

import cf_xarray as cfxr  # noqa
import numpy as np
import xarray as xr


def seed_patch(
    lon_ind_min: int,
    lon_ind_max: int,
    lat_ind_min: int,
    lat_ind_max: int,
    experiment_name: str = "as_patch",
    max_as_diff: bool = False,
    vertical_ind: int = 1,
    directional_filter: int = 0,
    grid_location: int = 0,
    file_target_dir: Optional[str] = None,
) -> None:
    """Create a seed-location file.

    Arguments
    =========
    lon_ind_min : int
        Lower boundary of seeding patch.
    lon_ind_max : int
        Upper boundary of seeding patch or delta relative to lower boundary if
        max_as_diff = True.
    lat_ind_min : int
        Left boundary of seeding patch.
    lat_ind_max: int
        Right boundary of seeding patch or delta relative to left boundary if
        max_as_diff = True.
    experiment_name : str
        Name of the output file will be `start_{experiment_name}.txt`
    max_as_diff : bool = False
        If False (default) use absolute index-values for upper and right patch boundary
        or if True use delta values relative to the lower and left patch boundary.
    directional_filter : int
        Release parcels only if the current flows
        northward/westward (1),
        southward/eastward (2),
        or in both direction (0, default).
    grid_location : int
        Set location within the grid where parcels are released,
        0 = zonal and meridional (default), 1 zonal, 2 meridional, 3 verdical.
    file_target_dir : str
        Use a target directory to save the seed-file, defaults to current work
        directory.

    Returns
    =======
    None
        Writes seed-file to disk.

    """
    if directional_filter not in [0, 1, 2]:
        raise ValueError("the directional filter (idir) must be in 0,1,2.")
    if grid_location not in [0, 1, 2, 3]:
        raise ValueError("grid location (isec) must be in 0,1,2,3.")

    seedfile = f"start_{experiment_name}.txt"
    if file_target_dir is not None:
        seedfile = str(Path(file_target_dir).joinpath(seedfile))
    else:
        seedfile = str(Path.home().joinpath("data", seedfile))
    with open(seedfile, "w") as file:
        ist_jst = [
            (ist, jst)
            for ist in range(
                lon_ind_min,
                lon_ind_min + lon_ind_max + 1 if max_as_diff else lon_ind_max + 1,
            )
            for jst in range(
                lat_ind_min,
                lat_ind_min + lat_ind_max + 1 if max_as_diff else lat_ind_max + 1,
            )
        ]
        for grid_loc in [[1, 2] if grid_location == 0 else [grid_location]][0]:
            for ist, jst in ist_jst:
                write_seed(file, ist, jst, vertical_ind, grid_loc, directional_filter)


def write_seed(
    file: io.TextIOWrapper,
    i: int,
    j: int,
    k: int = 1,
    gridloc: int = 1,
    dirfilt: int = 0,
) -> None:
    """Write single seed location to seed file."""
    file.write(
        "{0: 10d}{1: 10d}{2: 10d}{3: 6d}{4: 12d}\n".format(
            i,
            j,
            k,
            gridloc,
            dirfilt,
        ),
    )


def seed_horizontal_diagonal(
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    da: xr.DataArray,
    flow_direction: Dict[str, int],
    nyq: int = 3,
    experiment_name: Optional[str] = "diagonal",
    file_target_dir: Optional[Path] = None,
) -> List[Tuple[int, int]]:
    """Create a seed file for a horizontal diagonal seeding line."""
    if x1 < x0:
        raise ValueError("x1 needs to be equal to, or east of x0.")
    xi, yi = _interpolate_on_step_function(x0, y0, x1, y1, da, nyq)
    coords = _step_function_gridbox_coords(xi, yi, da)
    if file_target_dir is not None:
        seedfile = f"seed_{experiment_name}.txt"
        seedfile = str(file_target_dir.joinpath(seedfile))
        prev = []
        with open(seedfile, "w") as file:
            for i in range(len(coords)):
                if not prev:
                    y = coords[i][1]
                    isec = 2
                else:
                    y, isec = seedloc_at(coords[i][1], coords[i - 1][1])
                curr = {
                    "i": coords[i][0],
                    "j": y,
                    "k": 1,
                    "gridloc": isec,
                    "dirfilt": flow_direction["zonal"]
                    if isec == 1
                    else flow_direction["meridional"],
                }
                if curr == prev:
                    continue
                write_seed(file, **curr)
                prev = curr

    return coords


def seedloc_at(y: int, prev_y: int) -> Tuple[int, int]:
    """Identity box border to place seeds on.

    Special case for y < y-1 with x = x-1.
    The seeds need to be placed in the previous box.
    """
    east = 1
    north = 2
    isec = north if _horizontal(y, prev_y) else east
    y = prev_y if y < prev_y else y
    return y, isec


def _horizontal(y1: int, y2: int) -> bool:
    return y1 == y2


def _interpolate_on_step_function(
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    da: xr.DataArray,
    nyq: int,
) -> Tuple[np.ndarray, np.ndarray]:
    num = int(
        np.max(
            [
                (end - start) / delta * nyq
                for start, end, delta in zip(
                    [x0, y0],
                    [x1, y1],
                    [np.mean(np.diff(da.cf[dim])) for dim in ["longitude", "latitude"]],
                )
            ],
        ),
    )
    xi, yi = [
        np.linspace(start=start, stop=end, num=num)
        for start, end in zip([x0, y0], [x1, y1])
    ]
    return xi, yi


def _step_function_gridbox_coords(
    xi: np.ndarray,
    yi: np.ndarray,
    da: xr.DataArray,
) -> List[Tuple[int, int]]:
    """Calculate unique coordinates of gridboxed of the seeding step-function."""
    coords = [
        (
            float(da.cf[coord].cf.sel(**{coord: value, "method": "nearest"}).values)
            for coord, value in zip(["longitude", "latitude"], [lon, lat])
        )
        for lon, lat in zip(xi, yi)
    ]
    coords = [
        (
            index(da, "longitude", x),
            index(da, "latitude", y),
        )
        for x, y in coords
    ]
    coords = sorted(
        set(coords),
        key=lambda x: (x[0], x[1] * 1 if yi[-1] >= yi[0] else -1),
    )
    coords.extend(
        [
            (
                coords[i][0],
                coords[i + 1][1],
            )
            for i in range(len(coords[:-1]))
            if coords[i][0] != coords[i + 1][0] and coords[i][1] != coords[i + 1][1]
        ],
    )
    return sorted(
        set(coords),
        key=lambda x: (x[0], x[1] * 1 if yi[-1] >= yi[0] else -1),
    )


def index(ds: Union[xr.DataArray, xr.Dataset], dim: str, loc: float) -> int:
    """Look up nearest index given a location."""
    islocarr = ds[dim] != ds.sel(**{dim: loc}, method="nearest")[dim]
    notloc = True
    i = 0
    while notloc:
        notloc = islocarr[i]
        i += 1
    return i - 1


def convert(
    da: xr.DataArray,
    idx: Union[float, np.ndarray],
) -> Union[float, np.ndarray]:
    """Convert index to coordinate."""
    mi = da.min().values
    ma = da.max().values
    le = len(da)
    return idx / (le - 1) * (ma - mi) + mi


def main() -> None:
    """Run module as script."""
    seed_patch(708, 5, 595, 5, max_as_diff=True)


if __name__ == "__main__":
    main()
