Generate HRP project datasets
=============================

Script to generate HDX datasets for Humanitarian Response Plan project lists.

Usage:

    $ cp config.py.TEMPLATE config.py
    $ vi config.py # add your CKAN authentication token
    $ pip3 install -r requirements.txt
    $ python3 make-hrp-datasets.py

**Note:** plan-data.json will need to be updated every year, then the script needs to be rerun.
