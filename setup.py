import re

from setuptools import setup, find_packages

readme = open("README.rst").read()

with open("iniesta/__init__.py", encoding="utf8") as f:
    version = re.search(r'__version__ = "(.*?)"', f.read()).group(1)


setup(
    name="iniesta",
    version=version,
    description="Messaging integration for insanic",
    long_description=readme,
    author="Kwang Jin Kim",
    author_email="kwangjinkim@gmail.com",
    url="https://github.com/crazytruth/iniesta",
    packages=find_packages(include=["iniesta"], exclude=["docs", "tests"]),
    include_package_data=True,
    install_requires=["insanic-framework", "aiobotocore>=0.12.0", "aioredlock"],
    license="MIT",
    zip_safe=False,
    keywords="iniesta",
    extras_require={"cli": ["Click>=7.0"]},
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3.6",
    ],
    entry_points={"console_scripts": ["iniesta=iniesta.cli:cli"]},
)
