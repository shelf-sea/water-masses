from __future__ import annotations

import calendar
import io
import os
import sys
from pathlib import Path
from typing import Optional

import numpy as np
import streamlit as st
import xarray as xr
from cartopy import crs as ccrs
from matplotlib import pyplot as plt
from mpl_toolkits.axes_grid1 import make_axes_locatable
from PIL import Image

print(sys.version)  # noqa
assert all([za == zb for za, zb in zip(sys.version_info, [3, 8, 2, "final", 0])])


class Defaults(object):
    """Some defaults."""

    def __init__(self) -> None:
        """Init."""
        self.available_years: list[int] = [1992, 2001]
        self.start_year: int = 1998
        self.vmin_slider: list[int] = []
        self.vmax_slider: list[int] = []
        for vnam, vnum in zip(["vmin", "vmax"], [35.0, 35.5]):
            setattr(self, f"{vnam}_slider", [30.0, 36.0, vnum, 0.1])
        self._salinity_slider: list[float] = [30.0, 36.0, np.nan, 0.1]
        self.contours_slider: list[int] = [11, 31, 11, 1]


def main():
    """Run streamlit app."""
    st.write("# Copernicus Salinity Data")
    st.sidebar.markdown("# Select Year and Month")
    overwrite = st.sidebar.button("Overwrite image!")
    defaults = Defaults()
    years = {
        year: index
        for index, year in enumerate(
            range(defaults.available_years[0], defaults.available_years[-1] + 1),
        )
    }
    year = st.sidebar.selectbox(
        "Select Year:", list(years.keys()), index=years[defaults.start_year]
    )
    months = {month_abbr: index for index, month_abbr in enumerate(calendar.month_abbr)}
    del months[""]
    month = months[
        st.sidebar.selectbox(
            "Select Month:", list(months.keys()), index=months["Feb"] - 1
        )
    ]
    vmin = st.sidebar.slider("vmin", *defaults.vmin_slider)
    vmax = st.sidebar.slider("vmax", *defaults.vmax_slider)
    N = st.sidebar.slider("N", *defaults.contours_slider)
    outimg = (
        Path.cwd()
        / ".generated_app_images"
        / f"sal{year}{month:0>2}{vmin}{vmax}{N}.png"
    )
    if overwrite or not outimg.exists():
        ds = load(year, month)
        # var = ds["so"].mean(dim="depth", skipna=True)
        var = ds["so"].isel(depth=0)
        # var = ds.isel(depth=0)
        image = sketchplot(var, vmin=vmin, vmax=vmax, N=N)
        image.save(outimg)
    else:
        image = Image.open(outimg)
    st.image(image)
    save_pdf = st.sidebar.button("Save image as PDF")
    if save_pdf:
        rgb = Image.new("RGB", image.size, (255, 255, 255))
        rgb.paste(image, mask=image.split()[3])
        rgb.save(outimg.with_suffix(".pdf"), "PDF", resoultion=1000.0)


def load(year: int, month: int) -> xr.Dataset:
    home = os.environ["HOME"]
    path = f"{home}/data/copernicus/SAL/mm/metoffice_foam1_amm7_NWS_SAL_mm{year}{month:0>2}.nc"
    ds = xr.open_dataset(path, chunks={"time": 10})
    return ds


def fig2img(fig: plt.figure) -> Image:
    buf = io.BytesIO()
    fig.savefig(buf, format="png")
    buf.seek(0)
    img = Image.open(buf)
    return img


def sketchplot(
    var: xr.Dataset,
    time: int = 0,
    radii: Optional[list[int]] = None,
    center: Optional[list[int]] = None,
    vmin: float = 34,
    vmax: float = 35.5,
    N: int = 21,
    projection: str = "Orthographic",
) -> Image:
    if radii is None:
        radii = [10, 8]
    if center is None:
        center = [-7, 56]
    extent = [
        center[0] - radii[0],
        center[0] + radii[0],
        center[1] - radii[1],
        center[1] + radii[1],
    ]
    fig, ax = plt.subplots(
        1,
        1,
        figsize=(8, 10),
        dpi=80,
        facecolor="w",
        edgecolor="k",
        subplot_kw={"projection": getattr(ccrs, projection)(*center)},
    )
    fig.subplots_adjust(hspace=0, wspace=0, top=0.925, left=0.1)

    for method in ["contourf", "contour"]:
        rc = dict(
            ax=ax,
            transform=ccrs.PlateCarree(),
            vmin=vmin,
            vmax=vmax,
            levels=np.linspace(vmin, vmax, 121),
            add_colorbar=False,
            cmap=plt.get_cmap("magma"),
        )
        if method == "contour":
            del rc["cmap"]
            rc["colors"] = "k"
            rc["alpha"] = 0.3
            rc["levels"] = np.linspace(vmin, vmax, N)
        globals()["h_" + method] = getattr(var.isel(time=time).plot, method)(**rc)
    ax.set_extent(extent)
    ax.coastlines("50m", alpha=0.5)

    divider = make_axes_locatable(ax)
    ax_cb = divider.new_horizontal(size="5%", pad=0.5, axes_class=plt.Axes)

    ax.gridlines(
        crs=getattr(ccrs, "PlateCarree")(),
        draw_labels=True,
        linewidth=2,
        color="gray",
        alpha=0.5,
        linestyle="--",
    )

    ax.get_figure().gca().set_title("")

    fig.add_axes(ax_cb)
    cbar = plt.colorbar(
        globals()["h_contourf"], cax=ax_cb, ticks=[rc["levels"][n] for n in [0, -1]]
    )
    cbar.add_lines(globals()["h_contour"])
    cbar.ax.set_yticklabels(["fresh", "salty"])

    fig.tight_layout()

    return fig2img(fig)


if __name__ == "__main__":
    main()
