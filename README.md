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

# Quick Charts

The script will default Quick Sets to all datasets. If you want to
change the Quick Charts, you can set up one model the way you want,
then use the separate
[add-quick-charts](https://github.com/OCHA-DAP/add-quick-charts)
script to propagage the change, with the following parameters.

**Pattern:** "``^hrp-projects-[a-Z]{3}$``"

**Org:** "``ocha-fts``"

**Model:** the dataset ID of the model dataset (e.g. "``hrp-projects-nga``")

# Requirements

This script requires Python3, and the ckanapi and requests
packages. See ``requirements.txt`` for any recent changes.

# License

This script is in the Public Domain, and comes with NO WARRANTY. See
UNLICENSE.md for details.
