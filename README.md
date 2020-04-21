Generate HRP project datasets
=============================

Script to generate HDX datasets for Humanitarian Response Plan project lists.

# Usage

    $ cp config.py.TEMPLATE config.py
    $ vi config.py # add your CKAN authentication token
    $ pip3 install -r requirements.txt
    $ python3 make-hrp-datasets.py

The script will scan plans from HPC.tools and pick all the ones that
are associated with the Humanitarian Programme Cycle and effective in
2015 or later. It will also update the dataset end dates to the end of
the current year, so it is safe to rerun in future years after 2020.

There is also a Makefile that will handle the last two steps (and set
up a dedicated Python3 virtual environment for running the script):

    $ cp config.py.TEMPLATE config.py
    $ vi config.py
    $ make run

# Adding Quick Charts

After running this script, it will be necessary to set up Quick Charts
manually for one of the datasets, then to use the separate
[add-quick-charts](https://github.com/OCHA-DAP/add-quick-charts)
script to copy that configuration to the other datasets.

**Pattern:** "``^hrp-projects-[A-Z]{3}$``"

**Org:** "``ocha-fts``"

# Requirements

This script requires Python3, and the ckanapi and requests packages.

# License

This script is in the Public Domain, and comes with NO WARRANTY. See
UNLICENSE.md for details.
