from setuptools import setup, find_packages


with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="cedric",
    version="0.0.4",
    author="Abhishek Choudhury",
    author_email="choudhuryabhishek76@gmail.com",
    description="Cedric is a Python library designed to streamline the process of setting up a Django application. ",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/pypa/cedric",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=["django", "requests", "art", "inquirer"],
    entry_points={"console_scripts": ["setup=src.cli:main"]},
)
