from pathlib import Path
from setuptools import setup, find_packages


install_requires = [
    "pytz",
    "requests",
    "lxml",
    "python-dateutil",
    "parsedatetime",
    "cached-property",
    "click",
    "pathlib",
    "configparser",
    "zope.interface",
    "attrs",
    "jsonpickle"
]


console_scripts = ["poker = poker.commands:poker"]


classifiers = [
    "Intended Audience :: Developers",
    "Programming Language :: Python",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3 :: Only",
    "Programming Language :: Python :: 3.6",
    "Programming Language :: Python :: 3.7",
]


setup(
    name="poker",
    version="0.30.3",
    description="Poker Framework",
    long_description=Path("README.rst").read_text(),
    classifiers=classifiers,
    keywords="poker",
    author="Kiss Gyorgy, Christoph Birk",
    author_email="kissgyorgy@me.com",
    url="https://github.com/chris060986/poker",
    license="MIT",
    packages=find_packages(),
    install_requires=install_requires,
    entry_points={"console_scripts": console_scripts},
    tests_require=["pytest", "coverage", "coveralls"],
)
