[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/python/black) [![Build Status](https://travis-ci.org/cle-b/httpdbg.svg?branch=master)](https://travis-ci.org/cle-b/httpdbg) [![PyPI version](https://badge.fury.io/py/httpdbg.svg)](https://badge.fury.io/py/httpdbg) [![Coverage Status](https://coveralls.io/repos/github/cle-b/httpdbg/badge.svg?branch=master)](https://coveralls.io/github/cle-b/httpdbg?branch=master)
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
-- -- -- httpdbg - recorded requests available at http://localhost:5000/ 
Python 3.8.2 (default, Jul 16 2020, 14:00:26) 
[GCC 9.3.0] on linux
Type "help", "copyright", "credits" or "license" for more information.
(InteractiveConsole)
>>> 
```

Perform HTTP requests (using the requests library for example).

You can inspect the HTTP requests directly in your web browser at http://localhost:5000.

### script

You can trace all the HTTP requests performed by a script

```
pyhttpdbg filename.py [arg1 --arg2 ...]
```

### pytest

You can trace all the HTTP requests performed during your tests

```
pyhttpdbg pytest [arg1 --arg2 ...]
```

## thanks

httpdbg is based on [VCR.py](https://vcrpy.readthedocs.io/). Thanks to Kevin McCarthy and to all the contributors of [VCR.py](https://github.com/kevin1024/vcrpy) for this awesome library.
