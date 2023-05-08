# -*- coding: utf-8 -*-
import os
import sys

pytest_plugins = ["pytester"]


if sys.version_info < (3, 7):
    # to fix an import problem with python 3.6 during the tests
    os.environ["PYTHONPATH"] = os.path.realpath(
        os.path.join(os.path.dirname(os.path.realpath(__file__)), "../../httpdbg")
    )
