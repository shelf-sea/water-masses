# -*- coding: utf-8 -*-
"""Read and manipulate SPG strength index."""

import pandas as pd
from scipy import signal
from pathlib import Path
import numpy as np
from datetime import datetime
import calendar

from . import constants


def assign2trj(df: pd.DataFrame, spgs_idx: pd.DataFrame) -> pd.DataFrame:
    """Add SPG strength index to trajectories."""

    def to_spgs_idx(date: datetime.date):
        return np.round(
            spgs_idx.loc[(date.year, calendar.month_name[date.month]), "PC2"],
            decimals=0,
        )

    query = "date >= '{0}' & date <= '{1}'".format(
        "-".join([str(n) for n in constants.Timespan().start.timetuple()[:3]]),
        "-".join([str(n) for n in constants.Timespan().end.timetuple()[:3]]),
    )
    df = df.query(query)
    df = df.assign(
        init=df.reset_index("date")["date"]
        .dt.date.groupby("id")
        .transform("max")
        .tolist(),
    )
    vspgsi = np.vectorize(to_spgs_idx)

    return df.assign(PC2=vspgsi(df.init))


def open_index(path: Path) -> pd.DataFrame:
    """Read SPG strength index."""
    spgsi = pd.read_csv(path, header=None, names=["PC1", "PC2"])
    dates = pd.date_range(
        start=constants.Timespan().start,
        end=constants.Timespan().end,
        freq="MS",
    )
    spgsi = spgsi.assign(date=dates)
    spgsi = spgsi.assign(year=dates.year)
    spgsi = spgsi.assign(month=dates.month_name())
    spgsi = spgsi.set_index(["year", "month"])

    return spgsi


def filter(
    spgsi: pd.DataFrame,
    order: int = 10,
    freq: float = 12,
    cutoff: float = 4,
) -> pd.DataFrame:
    """Apply low pass filter."""
    nyq = 0.5 * freq
    sos = signal.butter(
        N=order,
        Wn=cutoff / nyq,
        btype="lowpass",
        fs=freq,
        output="sos",
    )
    spgsi["filtered"] = signal.sosfiltfilt(sos, spgsi.PC2)
    return spgsi
