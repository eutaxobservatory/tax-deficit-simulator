from setuptools import find_packages
from setuptools import setup

with open('requirements.txt') as f:
    content = f.readlines()
requirements = [x.strip() for x in content if 'git+' not in x]

setup(
    name='tax_deficit_simulator',
    version="1.0",
    description="Python package and online simulator accompanying the EU Tax Observatory's report of June 2021.",
    packages=find_packages(),
    test_suite='tests',
    zip_safe=False
)
