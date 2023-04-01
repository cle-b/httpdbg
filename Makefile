.PHONY: setup format lint test allpytest clean ci coverage selenium testui testall ciall typing check

setup:
	pip install -e .
	pip install -r requirements-dev.txt
	pip install -r requirements-dev-ui.txt

format:
	black httpdbg tests

lint:
	black --check httpdbg tests
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
	pip install -r requirements-dev.txt
	pip install .
	python -m pytest -v -m "not ui" tests/ --ignore=tests/ui/
coverage:
	coverage run -m pytest -v tests/

selenium:
	docker run -d --rm --network="host" -v /dev/shm:/dev/shm selenium/standalone-chrome:latest 

testui:
	pytest -v -m ui --driver Remote --capability browserName chrome tests/

testall:
	pytest -v --driver Remote --capability browserName chrome tests/

ciall:
	python -m pip install pip --upgrade
	pip install -r requirements-dev.txt
	pip install -r requirements-dev-ui.txt
	pip install .
	coverage run -m pytest -v --driver Remote --capability browserName chrome tests/

typing:
	mypy

check: lint typing
