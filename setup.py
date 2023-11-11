from setuptools import setup, find_packages


with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="yesabhishek",
    version="0.0.1",
    author="Abhishek Choudhury",
    author_email="choudhuryabhishek76@gmail.com",
    description="Gecko is a Python library designed to streamline the process of setting up a Django application. ",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/pypa/gecko",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)