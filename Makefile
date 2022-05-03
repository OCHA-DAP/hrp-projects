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

run: $(VENV)
	. $(VENV) && python $(SCRIPT)

build-venv: $(VENV)

$(VENV): requirements.txt
	rm -rf venv && python3 -m venv venv && . $(VENV) && pip install -r requirements.txt

clean:
	rm -rf venv

push:
	git push origin master
