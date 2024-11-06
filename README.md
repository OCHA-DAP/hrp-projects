Generate HRP project datasets
=============================

Script to generate HDX datasets for Humanitarian Response Plan project lists.

These script will scan plans from HPC.tools and pick all the ones that
are associated with the Humanitarian Programme Cycle and effective
five or fewer years ago. They save that information to a JSON file
that can be provided as input to a second script that updates or
creates datasets on HDX, with Quick Charts.


# Usage

## Running commands individually

    $ cp config.py.TEMPLATE config.py
    $ vi config.py # add your CKAN authentication token
    $ pip3 install -r requirements.txt
    $ mkdir output
    $ python3 scan-hrp-projects.py > output/hrp-scan.json
    $ python3 make-hrp-datasets.py output/hrp-scan.json
    
## Using the Makefile

There is also a Makefile that will handle the last two steps (and set
up a dedicated Python3 virtual environment for running the script):

    $ cp config.py.TEMPLATE config.py
    $ vi config.py
    $ make all


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
packages. See ``[requirements.txt](requirements.txt`` for any recent changes.


# License

This script is in the Public Domain, and comes with NO WARRANTY. See
``[UNLICENSE.md](UNLICENSE.md)`` for details.


# Author

Started 2020 by David Megginson.
