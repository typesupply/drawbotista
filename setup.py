#!/usr/bin/env python

from setuptools import setup, find_packages

setup(
    name="drawbotista",
    version="0.1",
    description="A port of a subset of the DrawBot API to Pythonista.",
    # long_description=long_description,
    author="Tal Leming",
    author_email="tal@typesupply.com",
    url="https://github.com/typesupply/drawbotista",
    license="MIT",
    package_dir={"": "Lib"},
    packages=find_packages("Lib"),
    install_requires=[]
)