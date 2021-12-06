# -*- coding: utf-8 -*-

from water_masses import version


def test_version():
    """Double check version."""
    assert version.pkg_version == "2021.3.10"
