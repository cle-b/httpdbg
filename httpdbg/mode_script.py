# -*- coding: utf-8 -*-
import importlib
import sys


def run_script(argv):
    sys.argv = argv
    try:
        spec = importlib.util.spec_from_file_location("torun", argv[0])
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    except Exception as exp:
        print(exp)
