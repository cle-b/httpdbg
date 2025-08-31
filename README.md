# httpdbg

`httpdbg` is a tool for Python developers to easily debug the HTTP(S) client and server requests in a Python program.

To use it, execute your program using the `pyhttpdbg` command instead of `python` and that's it. Open a browser to `http://localhost:4909` to view the requests:

![](https://github.com/cle-b/httpdbg/blob/main/ui.png?raw=true)

Supports `HTTP/1.0`, `HTTP/1.1`, and `HTTP/2`.

Full documentation => [https://httpdbg.readthedocs.io/](https://httpdbg.readthedocs.io/en/latest/)

## installation 

```
pip install httpdbg
```

## usage

By default, both client and server requests are recorded. To record only client requests, use the `--only-client` command line argument.

### interactive console

Open an interactive console using the command `pyhttpdbg`.

```console
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

### script

You can trace all the HTTP requests performed by a script

```console
pyhttpdbg --script filename.py [arg1 --arg2 ...]
```

### module

You can trace all the HTTP requests performed by a library module run as a script using the `-m` command line argument.

For example, you can view which HTTP requests are performed by `pip` when you install a package.

```console
pyhttpdbg -m pip install hookdns --upgrade
```

### test frameworks

You can trace all HTTP requests made during your tests (pytest, unittest).

```console
pyhttpdbg -m pytest [arg1 --arg2 ...]
```

In that case, the requests will be grouped by test, and any requests made within a fixture or the setup/teardown methods will be identified by a tag.


### HTTP server

You can trace all HTTP requests received by your HTTP server.

```console
pyhttpdbg -m flask --app demoflask run
.... - - .--. -.. -... --. .... - - .--. -.. -... --. .... - - .--. -.. -... --.
  httpdbg - HTTP(S) requests available at http://localhost:4909/
.... - - .--. -.. -... --. .... - - .--. -.. -... --. .... - - .--. -.. -... --.
 * Serving Flask app 'demoflask'
 * Debug mode: off
WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.
 * Running on http://127.0.0.1:5000
Press CTRL+C to quit
127.0.0.1 - - [14/Mar/2025 17:47:42] "GET / HTTP/1.1" 200 -
127.0.0.1 - - [14/Mar/2025 17:47:50] "GET /hello/Ben HTTP/1.1" 200 -
127.0.0.1 - - [14/Mar/2025 17:47:56] "GET /oups HTTP/1.1" 404 -
```

![httpdbg 1.1.0 - pyhttpdbg -m flask --app demoflask run](https://github.com/cle-b/httpdbg/blob/main/ui_server.png?raw=true)


## initiators and groups
 
An initiator is the function/method that is at the origin of the HTTP requests. By default, we already support some packages but you can add your own initiators. 

To add a new package in the list of initiators, you can use the `-i` command line argument:

```console
pyhttpdbg -i api_client_pck --script my_script.py
```

You can use any package as an initiator, this is not limited to HTTP requests.

### supported HTTP client

The initiator is the highest-level method used to make the request through the client. The group and the initiator are identical. If a request to a URL generates multiple requests, as in the case of redirection, all these requests will be grouped together.

| packages       | status                              | initiator | group     |
|----------------|-------------------------------------|-----------|-----------|
| requests       | supported                           | yes       | yes       |
| urllib3        | supported                           | yes       | yes       |
| httpx          | supported                           | yes       | yes       |
| aiohttp        | supported                           | yes       | yes       |
| _your_package_ | yes, with the arg _-i your_package_ | yes       | yes       |

### supported HTTP server

The initiator is the low-level socket method that receives the data. The group is the endpoint method used to handle the request. A client request made within the endpoint method will be included in this group.

| packages       | status                              | initiator | group     |
|----------------|-------------------------------------|-----------|-----------|
| flask          | supported                           | -         | yes       |
| fastapi        | supported                           | -         | yes       |

### supported test framework

The requests are grouped by tests.

| packages       | status                              | initiator | group     |
|----------------|-------------------------------------|-----------|-----------|
| pytest         | supported                           | -         | yes       |
| unittest       | supported                           | -         | yes       |

### supported HTTP version

| version        | status                                                      |     
|----------------|-------------------------------------------------------------|
| 1.0            | supported                                                   |
| 1.1            | supported                                                   |
| 2              | supported (only through the `h2` lib)                       |



## configuration

No configuration is necessary to start but some few settings are available for particular use.

### command line

```console
usage: pyhttpdbg [-h] [--host HOST] [--port PORT] [--version]
                 [--initiator INITIATOR] [--only-client]
                 [--keep-up | --force-quit]                 
                 [--console | --module MODULE | --script SCRIPT]

httdbg - a very simple tool to debug HTTP(S) client requests

options:
  -h, --help            show this help message and exit
  --host HOST           the web interface host IP address
  --port PORT, -p PORT  the web interface port
  --version, -v         print the httpdbg version
  --initiator INITIATOR, -i INITIATOR
                        add a new initiator (package)
  --only-client         record only HTTP client requests
  --keep-up, -k         keep the server up even if the requests have been read
  --force-quit, -q      stop the server even if the requests have not been read
  --console             run a python console (default)
  --module MODULE, -m MODULE
                        run library module as a script (the next args are passed to pytest as is)
  --script SCRIPT       run a script (the next args are passed to the script as is)
```

### web interace 

Some options are available to customize the UI:

  * Change the strategy to group the requests.
  * Hide the scheme and the network location in the url.
  * Hide the group rows.
  * Hide the tags.
  * ...

You can also pin a request or delete all unpinned requests.

To keep your configuration, bookmark the page with the full search query.

Fox example, if you want to hide the group rows by default, the url will be:
```
http://localhost:4909/?hi=on
```

## web interface

All the requests recorded are available on the web interface. 

The requests:
 * are still available in the web page even if the python process stopped (except if you force quit before the requests have been loaded by the web page).
 * are automatically cleaned if a new execution is detected.

## limitations

Theoretically, if your HTTP client or server uses a standard Python socket, the HTTP requests will be recorded.

Support for recording requests on the server side is new in `httpdbg 1.0.0`. In some cases, like with |FastAPI| using |uvloop|, we had to implement a new mechanism to make request recording possible. This is still a work in progress as we aim to support more frameworks.

## documentation

https://httpdbg.readthedocs.io
