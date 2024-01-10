# -*- coding: utf-8 -*-
import importlib
import sys
import traceback
from typing import List


def run_script(argv: List[str]) -> None:
    sys.argv = argv
    if len(argv) == 0:
        exit("script mode - error - python file required, but none set")
    try:
        spec = importlib.util.spec_from_file_location("torun", argv[0])  # type: ignore
        module = importlib.util.module_from_spec(spec)  # type: ignore
    except AttributeError:
        exit("script mode - error - the first argument shall be a python file")
    try:
        spec.loader.exec_module(module)  # type: ignore
    except Exception:
        traceback.print_exc()
