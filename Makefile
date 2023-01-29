.PHONY: setup format lint test allpytest clean ci coverage selenium testui testall ciall

setup:
	pip install -e .
	pip install -r requirements-dev.txt

format:
	black httpdbg tests setup.py

lint:
	black --check httpdbg tests setup.py
	flake8 httpdbg tests

test:
	pytest -v -m "not ui" tests/

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

selenium:
	docker run --rm --network="host" -v /dev/shm:/dev/shm selenium/standalone-chrome:latest 

testui:
	pytest -v -m ui --driver Remote --capability browserName chrome tests/

testall:
	pytest -v --driver Remote --capability browserName chrome tests/

ciall:
	python -m pip install pip --upgrade
	pip install .
	pip install -r requirements-dev.txt
	coverage run -m pytest -v --driver Remote --capability browserName chrome tests/
