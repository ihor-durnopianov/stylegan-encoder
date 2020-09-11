#

SHELL := /bin/bash

.ONESHELL:

# env:
# 	python -m venv env
# 	source env/bin/activate
# 	pip install --upgrade pip
# 	pip install wheel
# 	pip install --requirement requirements-dev.txt
# 	pip install --requirement requirements.txt
# 	pip install --editable .

# test: env
# 	source env/bin/activate
# 	pytest .

lint: # env
	source env/bin/activate
	pylint encoder.py

build:
	nbsync.py -mf -d "" dev/encode.ipynb encoder.py
