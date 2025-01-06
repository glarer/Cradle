## usage: python3 setup.py build_ext --inplace

from setuptools import setup, Extension

rdtsc_module = Extension(
    'rdtsc', 
    sources=['rdtsc.c'],
)

setup(
    name='rdtsc',
    version='1.0',
    description='Python wrapper for rdtsc instruction',
    ext_modules=[rdtsc_module],
)

