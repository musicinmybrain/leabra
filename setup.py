"""Setup script

For details: https://packaging.python.org/en/latest/distributing.html
"""
import os
import setuptools


here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'readme.md'), encoding='utf-8') as fd:
    long_description = fd.read()


setuptools.setup(
    name='leabra-psyneulink',
    version='0.3.2',

    description='Python implementation of the Leabra algorithm. Forked to package and upload to PyPi.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/dillontsmith/leabra',

    author='Fabien C. Y. Benureau',
    author_email='fabien.benureau@gmail.com',

    license='GPLv3',

    keywords='computational neuroscience, emergent, leabra',

    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        'Development Status :: 3 - Alpha',

        'Intended Audience :: Science/Research',
        'Intended Audience :: Developers',
        'Intended Audience :: Education',

        'Topic :: Scientific/Engineering',
        'Topic :: Scientific/Engineering :: Artificial Life',

        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',

        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],

    # where is our code
    packages=['leabra'],

    # required dependencies
    install_requires=['numpy', 'scipy', 'bokeh>=0.12.6', 'ipywidgets>=7.0', 'jupyter'],

    # you can install extras_require with
    # $ pip install -e .[test]
    extras_require={'test': ['pytest', 'pytest-cov']},
)
