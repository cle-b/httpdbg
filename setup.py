# -*- coding: utf-8 -*-
import setuptools

with open("README.md", "r") as fh:
    # remove badges and screenshot
    lines = []
    for line in fh.readlines()[1:]:
        if "![ui]" not in line:
            lines.append(line)
    long_description = "".join(lines)

setuptools.setup(
    name="httpdbg",
    version="0.1.1",
    author="cle-b",
    author_email="cle@tictac.pm",
    description="A very simple tool to debug HTTP(S) client requests",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/cle-b/httpdbg",
    packages=setuptools.find_packages(),
    package_data={"httpdbg": ["webapp/static/*"]},
    python_requires=">=3.6",
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
