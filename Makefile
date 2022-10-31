.PHONY: prepare format lint test clean

setup:
	pip install -e .
	pip install -r requirements-dev.txt

format:
	black httpdbg tests setup.py

lint:
	black --check httpdbg tests setup.py
	flake8 httpdbg tests

test:
	pytest -v

allpytest:
	tox -e pytest4 -e pytest5 -e pytest6 -e pytest7

clean:
	rm -rf .pytest_cache
	rm -rf __pycache__
	rm -rf httpdbg.egg-info
	rm -rf venv

ci:
	python -m pip install pip --upgrade
	pip install .
	pip install -r requirements-dev.txt
	pytest -v tests/

coverage:
	coverage run -m pytest -v tests/
