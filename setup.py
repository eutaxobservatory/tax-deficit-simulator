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
    zip_safe=False,
    install_requires=[
        "pip>=9"
        "setuptools>=26"
        "wheel>=0.29"
        "pandas>=1.1.3"
        "numpy>=1.18.5"
        "scipy>=1.6.1"
        "openpyxl>=3.0.7"
        "pycountry==20.7.3"
    ],
    include_package_data=True,
    package_data={
        "tax_deficit_simulator": [
            "data/*.csv", "data/*.xlsx",
            "data/firm_level_cbcrs/*.csv",
            "data/TWZ/*.xlsx", "data/TWZ/2016/*.xlsx", "data/TWZ/2017/*.xlsx", "data/TWZ/2018/*.xlsx"
        ]
    }
)
