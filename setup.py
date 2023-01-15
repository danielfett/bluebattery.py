import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="bluebattery.py",
    version="1.0.0",
    author="Daniel Fett",
    author_email="mail@danielfett.de",
    description="Software for interacting with the BlueBattery line of battery computers.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/danielfett/bluebattery.py",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    install_requires=[
        "bleak",
        "py-flags",
        "coloredlogs",
        "paho-mqtt",
        "hummable",
    ],
    entry_points={
        "console_scripts": [
            "bb_cli=bluebattery.cli:run",
        ],
    },
)
