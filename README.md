[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/python/black) [![Build Status](https://github.com/cle-b/httpdbg/workflows/Build/badge.svg?branch=main)](https://github.com/cle-b/httpdbg/actions?query=workflow%3ABuild) [![PyPI version](https://badge.fury.io/py/httpdbg.svg)](https://badge.fury.io/py/httpdbg) [![Coverage Status](https://coveralls.io/repos/github/cle-b/httpdbg/badge.svg?branch=main)](https://coveralls.io/github/cle-b/httpdbg?branch=main)
# httpdbg

A very simple tool to debug HTTP(S) client requests.

![ui](ui.png)
## installation 

```
pip install httpdbg
```

## usage

### interactive console

Open an interactive console using the following command: `pyhttpdbg`

```
(venv) dev@host:~/dir$ pyhttpdbg 
.... - - .--. -.. -... --. .... - - .--. -.. -... --. .... - - .--. -.. -... --.
  httpdbg - HTTP(S) requests available at http://localhost:4909/
.... - - .--. -.. -... --. .... - - .--. -.. -... --. .... - - .--. -.. -... --.
Python 3.10.6 (main, Aug 10 2022, 11:40:04) [GCC 11.3.0] on linux
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

*note: the HTTP(S) requests are not recorded if the tests are executed in parallel using plugin like `xdist`*.

## configuration

No configuration is necessary to start but some few settings are available for particular use.

### command line

```
usage: pyhttpdbg [-h] [--port PORT] [--version] [--keep-up | --force-quit]
                 [--console | --pytest | --script]

httdbg - a very simple tool to debug HTTP(S) client requests

options:
  -h, --help            show this help message and exit
  
  --port PORT, -p PORT  the web interface port
  
  --version, -v         print the httpdbg version

  --keep-up, -k         keep the server up even if the requests have been read
  --force-quit, -q      stop the server even if the requests have not been read

  --console             run a python console
  --pytest              run pytest (the next args are passed to pytest as is)
  --script              run the script that follows this arg (the next args are passed to the script as is)
                        
```

### web interace 

Clic on the **&#9881;** button on the top right of the page.

Many options are available:
  * Hide the status column
  * Hide the method column
  * Hide the netloc in the url
  * Hide the initiator column

To keep your configuration, bookmark the page with the full search query.

Fox example, if you want to keep only the `status` and `url` columns, the url will be:
```
http://localhost:4909/?hm=on&hi=on
```

## web interface

All the requests recorded are available on the web interface. 

The requests:
 * are still available in the web page even if the python process stopped (except if you force quit before the requests have been loaded by the web page).
 * are automatically cleaned if a new execution is detected.
