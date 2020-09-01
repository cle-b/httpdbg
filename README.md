[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/python/black)

# httpdbg

A very simple tool to debug HTTP client requests

## installation 

```
pip install httpdbg
```

## usage

Open an interactive console with the following command

```
python -m httpdbg
```

Perform HTTP requests (using the requests library for example).

You can inspect the HTTP requests directly in your web browser at http://localhost:5000.

## thanks

httpdbg is based on [VCR.py](https://vcrpy.readthedocs.io/). Thanks to Kevin McCarthy and to all the contributors of [VCR.py](https://github.com/kevin1024/vcrpy) for this awesome library.
