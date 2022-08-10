.PHONY: prepare format lint test clean

SHELL := /bin/bash

prepare:
	python3 -m venv venv ;\
	source venv/bin/activate ;\
	pip install pip --upgrade ;\
	pip install -e . ;\
	pip install -r requirements-dev.txt

format:
	black httpdbg tests setup.py

lint:
	black --check httpdbg tests setup.py
	flake8 httpdbg tests

test:
	pytest -v

clean:
	rm -rf .pytest_cache
	rm -rf __pycache__
	rm -rf httpdbg.egg-info
	rm -rf venv
