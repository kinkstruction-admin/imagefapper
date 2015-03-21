import setuptools
from imagefapper._version import __version__


try:
    with open("README.rst") as f:
        long_description = f.read()
except IOError:
    long_description = ""

try:
    with open("requirements.txt") as f:
        requirements = [x for x in [y.strip() for y in f.readlines()] if x]
except IOError:
    requirements = []

setuptools.setup(
    install_requires=requirements,
    version=__version__,
    name="imagefapper",
    license="MIT",
    author="Jack Maney",
    author_email="jackmaney@gmail.com",
    packages=setuptools.find_packages(),
    long_description=long_description,
    entry_points={
        "console_scripts": [
            "imagefapper=imagefapper.imagefapper:main"
        ]
    }
)
