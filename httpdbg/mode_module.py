# -*- coding: utf-8 -*-
import runpy
from unittest.mock import patch
import sys
from typing import List


def run_module(argv: List[str]) -> None:
    try:
        with patch.object(sys, "argv", argv):
            runpy.run_module(argv[0], run_name="__main__")
    except SystemExit:
        pass
