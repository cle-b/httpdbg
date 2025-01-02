# -*- coding: utf-8 -*-
import importlib
import sys
import traceback
from typing import List

from httpdbg.log import logger


def run_script(argv: List[str]) -> None:
    sys.argv = argv
    if len(argv) == 0:
        exit("script mode - error - python file required, but none set")
    try:
        spec = importlib.util.spec_from_file_location("__main__", argv[0])  # type: ignore
        module = importlib.util.module_from_spec(spec)  # type: ignore
    except AttributeError:
        exit("script mode - error - the first argument shall be a python file")
    try:
        original__main___module = sys.modules["__main__"]
        sys.modules["__main__"] = module  # mandatory to execute a unittest test file.
        spec.loader.exec_module(module)  # type: ignore
    except Exception:
        traceback.print_exc()
    except SystemExit as ex:
        # in some case, for example when executing unittest tests from a script,
        # the SystemExit exception is raised by the script itself so we catch it.
        # TODO propagate the SystemExit value when httpdbg terminates.
        logger().info(f"run_script - exception SystemExit - {str(ex)}")
    finally:
        sys.modules["__main__"] = original__main___module
