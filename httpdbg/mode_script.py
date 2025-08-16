# -*- coding: utf-8 -*-
import os
import runpy
import sys
import traceback

from httpdbg.log import logger


def run_script(argv: list[str]) -> None:

    if len(argv) == 0:
        exit("script mode - error - python file required, but none set")

    try:
        original_sys_path = sys.path
        original_sys_argv = sys.argv

        sys.path.insert(0, os.path.abspath(argv[0]))
        sys.argv = argv

        runpy.run_path(argv[0], run_name="__main__")
    except SystemExit as ex:
        # in some case, for example when executing unittest tests from a script,
        # the SystemExit exception is raised by the script itself so we catch it.
        # TODO propagate the SystemExit value when httpdbg terminates.
        logger().info(f"run_script - exception SystemExit - {str(ex)}")
    except Exception:
        traceback.print_exc()
    finally:
        sys.path = original_sys_path
        sys.argv = original_sys_argv
