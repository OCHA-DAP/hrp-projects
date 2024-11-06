#########################################################################
# Makefile for the the hpc-projects script
#
# Targets:
#
# run: run the script, building the Python3 virtual environment if needed
# build-venv: rebuild the virtual environment if needed
# push: push the master branch to GitHub
#
# You must copy config.py.TEMPLATE to config.py first, and fill in
# the appropriate values.
########################################################################

VENV=venv/bin/activate
SCRIPT=make-hrp-datasets.py

SCANNED_DATA=output/hrp-scan.json

all: scan-hpc-tools update-hdx

run: $(VENV)
	. $(VENV) && python $(SCRIPT)

update-subnational: $(VENV)
	. $(VENV) && python update-subnational-flags.py

scan-hpc-tools: $(VENV)
	. $(VENV) && mkdir -p output && python3 scan-hrp-projects.py > $(SCANNED_DATA)

update-hdx: $(VENV)
	. $(VENV) && python3 make-hrp-datasets.py $(SCANNED_DATA)

build-venv: $(VENV)

$(VENV): requirements.txt
	rm -rf venv && python3 -m venv venv && . $(VENV) && pip install -r requirements.txt

clean:
	rm -rf venv

push:
	git push origin master
