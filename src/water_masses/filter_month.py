# -*- coding: utf-8 -*-
"""Read from initial conditions for subsampling.

Use data set of initial values to first, select a specific
initialization-month and then subsample in that month.
"""


from pathlib import Path
from typing import Optional

import pandas as pd

from .constants import Timespan


class MetaData(object):
    """Define general meta data."""

    def __init__(
        self, data_path: Optional[str] = None, timespan: Optional[Timespan] = None
    ) -> None:
        """Init."""
        self.data_path = (
            data_path
            if data_path is not None
            else str(
                Path.home().joinpath(
                    "data",
                    "interim",
                    "tracmass_out",
                    "tests_{0}.csv",
                ),
            )
        )
        self.timespan = timespan if timespan is not None else Timespan()

    import_kwargs = {
        "header": None,
        "usecols": [0, 1, 5],
        "names": ["id", "lon", "time"],
        "skipinitialspace": True,
    }
    indices = ["id"]


def open_dataset(data_name: str, meta_data) -> pd.DataFrame:
    """Open dataset given the Intake sources name."""
    df = pd.read_csv(  # type: ignore
        meta_data.data_path.format(data_name),
        **meta_data.import_kwargs,
    ).set_index(meta_data.indices)
    df = df.assign(
        date=pd.Timestamp(meta_data.timespan.end)
        + pd.to_timedelta(df.time.values, "s"),
    )
    df.set_index([df.index, "date"], inplace=True)
    return df


def select_from_initialization(
    sample_size: int = 4,
    month: str = "January",
    meta_data: Optional[MetaData] = None,
) -> pd.Int64Index:
    """Filter for month and draw random sample.

    First open initialization data of trajectpries, then Filter for month and draw
    random sample.

    """
    if meta_data is None:
        meta_data = MetaData()
    df = open_dataset("ini", meta_data)
    of_month = df.index.get_level_values("date").month_name() == month
    return df[of_month].sample(sample_size).index.get_level_values("id")


def main() -> pd.Int64Index:
    """Return 100 samples from January initialization indices of test run."""
    return select_from_initialization(sample_size=100)


if __name__ == "__main__":
    main()
