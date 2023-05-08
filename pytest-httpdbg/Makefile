.PHONY: setup format lint check test clean ci 

setup:
	pip install -e .
	pip install -r requirements-dev.txt

format:
	black pytest_httpdbg tests

lint:
	black --check pytest_httpdbg tests
	flake8 pytest_httpdbg tests

check: lint

test:
	pytest -v tests/

clean:
	rm -rf .pytest_cache
	rm -rf __pycache__
	rm -rf pytest_httpdbg.egg-info
	rm -rf venv
	rm -rf build
	rm -rf dist

ci:
	python -m pip install pip --upgrade
	python -m pip install setuptools wheel --upgrade
	pip install -r requirements-dev.txt
	pip install .
	python -m pytest -v tests/
