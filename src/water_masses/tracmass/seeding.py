# -*- coding: utf-8 -*-
"""Create seeding file for Tracmass."""
from typing import Optional
from pathlib import Path


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
                file.write(
                    "{0: 10d}{1: 10d}{2: 10d}{3: 6d}{4: 12d}\n".format(
                        ist,
                        jst,
                        vertical_ind,
                        grid_loc,
                        directional_filter,
                    ),
                )


def main() -> None:
    """Run module as script."""
    seed_patch(708, 5, 595, 5, max_as_diff=True)


if __name__ == "__main__":
    main()
