# water-masses

[![Build
Status](https://travis-ci.com/shelf-sea/water-masses.svg?branch=master)](https://travis-ci.com/shelf-sea/water-masses)
[![Coverage](https://coveralls.io/repos/github/shelf-sea/water-masses/badge.svg?branch=master)](https://coveralls.io/github/shelf-sea/water-masses?branch=master)
[![Python
Version](https://img.shields.io/pypi/pyversions/water-masses.svg)](https://pypi.org/project/water-masses/)
[![wemake-python-styleguide](https://img.shields.io/badge/style-wemake-000000.svg)](https://github.com/wemake-services/wemake-python-styleguide)

On the origin of water masses in the northern European shelf seas from a Lagrangian
perspective


## Features

- Fully typed with annotations and checked with mypy, [PEP561
  compatible](https://www.python.org/dev/peps/pep-0561/)
- Add yours!


## Installation

This package uses [Cartopy](https://scitools.org.uk/cartopy/docs/latest/gallery/index.html)
which unfortunately has
[dependencies]((https://scitools.org.uk/cartopy/docs/latest/installing.html)) outside of
python, thus

1. On Ubuntu (did not work so far)

```bash
sudo apt-get install libproj-dev proj-data proj-bin
sudo apt-get install libgeos++-dev
```

2. On MacOS (see [this
   issue](https://github.com/SciTools/cartopy/issues/1288#issuecomment-491100316))

```bash
brew install geos
brew uninstall proj
brew tap-new $USER/local-tap
brew extract --version=5.2.0 proj $USER/local-tap
brew install proj@5.2.0
```


3. Install package itself

```bash
git clone <water-masses>
cd water-masses
poetry install
```


## Example

Showcase how your project can be used:

```python
from water_masses.example import some_function

print(some_function(3, 4))
# => 7
```

## License

[gpl3](https://github.com/shelf-sea/water-masses/blob/master/LICENSE)


## Credits

This project was generated with
[`wemake-python-package`](https://github.com/wemake-services/wemake-python-package). Current
template version is:
[bb8c7926355bcd126f198eba30fa0d51b2af5252](https://github.com/wemake-services/wemake-python-package/tree/bb8c7926355bcd126f198eba30fa0d51b2af5252).
See what is
[updated](https://github.com/wemake-services/wemake-python-package/compare/bb8c7926355bcd126f198eba30fa0d51b2af5252...master)
since then.
