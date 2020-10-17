# -*- coding: utf-8 -*-
import sys


def run_pytest(argv):
    sys.argv = argv

    import pytest  # we import pytest here to not be dependant to pytest if the user don't need it

    pytest.main()
