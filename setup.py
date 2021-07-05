import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="bluebattery.py",
    version="0.0.1",
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
        "gatt",
        "py-flags",
    ],
    entry_points={
        "console_scripts": [
            "bb_cli=bluebattery.cli:cli",
            "bb_mqtt=bluebattery.cli:mqtt",
            "bb_live=bluebattery.cli:live",
        ],
    },
)
