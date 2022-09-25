# -*- coding: utf-8 -*-
import importlib
import sys
import traceback


def run_script(argv):
    sys.argv = argv
    if len(argv) == 0:
        exit("script mode - error - python file required, but none set")
    try:
        spec = importlib.util.spec_from_file_location("torun", argv[0])
        module = importlib.util.module_from_spec(spec)
    except AttributeError:
        exit("script mode - error - the first argument shall be a python file")
    try:
        spec.loader.exec_module(module)
    except Exception:
        traceback.print_exc()
