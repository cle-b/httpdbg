.PHONY: prepare linter test clean

SHELL := /bin/bash

prepare:
	python3 -m venv venv ;\
	source venv/bin/activate ;\
	pip install pip --upgrade ;\
	pip install -e . ;\
	pip install -r requirements-dev.txt

formater:
	black httpdbg tests setup.py

linter: formater
	flake8 httpdbg tests

test:
	pytest -v

clean:
	rm -rf .pytest_cache
	rm -rf __pycache__
	rm -rf httpdbg.egg-info
	rm -rf venv
