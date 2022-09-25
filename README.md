[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/python/black) [![Build Status](https://github.com/cle-b/httpdbg/workflows/Build/badge.svg?branch=master)](https://github.com/cle-b/httpdbg/actions?query=workflow%3ABuild) [![PyPI version](https://badge.fury.io/py/httpdbg.svg)](https://badge.fury.io/py/httpdbg) [![Coverage Status](https://coveralls.io/repos/github/cle-b/httpdbg/badge.svg?branch=master)](https://coveralls.io/github/cle-b/httpdbg?branch=master)
# httpdbg

A very simple tool to debug HTTP client requests

## installation 

```
pip install httpdbg
```

## usage

### interactive console

Open an interactive console with the following command

```
pyhttpdbg
```
```
(venv) dev@host:~/dir$ pyhttpdbg
-- -- -- httpdbg - recorded requests available at http://localhost:4909/ 
Python 3.8.2 (default, Jul 16 2020, 14:00:26) 
[GCC 9.3.0] on linux
Type "help", "copyright", "credits" or "license" for more information.
(InteractiveConsole)
>>> 
```

Perform HTTP requests.

You can inspect the HTTP requests directly in your web browser at http://localhost:4909.

*note: we only intercept the requests done using `requests`*.

### script

You can trace all the HTTP requests performed by a script

```sh
pyhttpdbg --script filename.py [arg1 --arg2 ...]
```

### pytest

You can trace all the HTTP requests performed during your tests

```sh
pyhttpdbg --pytest [arg1 --arg2 ...]
```
