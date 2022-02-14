import gzip
from pathlib import Path
from typing import Union

import pandas as pd
import vaex


def open_tracmass_file(
    filepath: Path, use_vaex: bool = True, convert=False
) -> Union[vaex.dataframe.DataFrameLocal, pd.DataFrame]:
    """Open tracmass as pandas dataframe or veax dataframe.

    Defaults to the use of vaex, otherwise uses pandas.

    """
    suffixes = _get_suffixes(filepath)
    kws = {
        "header": None,
        "names": ["id", "i", "j", "k", "subvol", "time"],
        "usecols": [0, 1, 2, 3, 4, 5],
    }
    if convert:
        kws["convert"] = convert
    if use_vaex and (suffixes == ".hdf5"):
        df = vaex.open(filepath)
    elif use_vaex and (suffixes == ".csv"):
        df = vaex.from_csv(filepath, **kws)
    elif use_vaex and (suffixes == ".csv.gz"):
        with gzip.open(filepath, "rb") as file:
            df = vaex.from_csv(file, **kws)
    else:
        df = pd.read_csv(filepath, **kws)

    return df


def _get_suffixes(path: Path) -> str:
    """Extract and check suffixes."""
    if "".join(path.suffixes[-1:]).lower() in [".hdf5", ".csv"]:
        suffixes = "".join(path.suffixes[-1:]).lower()
    elif "".join(path.suffixes[-2:]).lower() == ".csv.gz":
        suffixes = "".join(path.suffixes[-2:]).lower()
    else:
        raise ValueError(
            "Unknown data format, known are CSV (including .csv.gz) and HDF5."
        )

    return suffixes
