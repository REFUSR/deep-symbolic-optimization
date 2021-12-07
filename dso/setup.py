from distutils.core import setup
import os
from setuptools import dist

required = [
    "pytest",
    "cython",
    "numpy<=1.19",
    "tensorflow==1.14",
    "numba==0.53.1",
    "sympy",
    "pandas",
    "scikit-learn",
    "click",
    "deap",
    "pathos",
    "seaborn",
    "progress",
    "tqdm",
    "commentjson",
    "PyYAML"
]

extras = {
    "control": [
        "mpi4py",
        "gym[box2d]==0.15.4",
        "pybullet",
        "stable-baselines[mpi]==2.10.0"
    ],
    "regression": []
}
extras['all'] = list(set([item for group in extras.values() for item in group]))

setup(  name='dso',
        version='1.0dev',
        description='Deep symbolic optimization.',
        author='LLNL',
        packages=['dso'],
        setup_requires=[],
        install_requires=required,
        extras_require=extras
        )
