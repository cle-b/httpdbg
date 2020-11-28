# -*- coding: utf-8 -*-
import os
import sys


def run_pytest(argv):
    sys.argv = argv

    # load a custom pytest plugin in order to link tests and requests
    path_to_pytest_plugin = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "pytest_plugin"
    )
    sys.path.append(path_to_pytest_plugin)

    pytest_plugins = os.environ.get("PYTEST_PLUGINS", "")
    if pytest_plugins != "":
        os.environ["PYTEST_PLUGINS"] = f"{pytest_plugins},httpdbg_pytest"
    else:
        os.environ["PYTEST_PLUGINS"] = "httpdbg_pytest"

    import pytest  # we import pytest here to not be dependant to pytest if the user don't need it

    pytest.main()
