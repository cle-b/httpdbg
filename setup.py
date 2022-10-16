# -*- coding: utf-8 -*-
import setuptools
from httpdbg import __VERSION__


with open("README.md", "r") as fh:
    # remove badges and screenshot
    long_description = "\n".join(fh.readlines()[1:-1])

setuptools.setup(
    name="httpdbg",
    version=__VERSION__,
    author="cle-b",
    author_email="cle@tictac.pm",
    description="A very simple tool to debug HTTP client requests",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/cle-b/httpdbg",
    packages=setuptools.find_packages(),
    package_data={"httpdbg": ["webapp/static/*"]},
    python_requires=">=3.6",
    install_requires=[
        "Jinja2<3.1",
        "Werkzeug<2.1",
        "flask>2",
        "flask-restful",
        "beautifulsoup4",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
    ],
    entry_points={
        "console_scripts": ["pyhttpdbg=httpdbg.__main__:pyhttpdbg_entry_point"],
    },
)
