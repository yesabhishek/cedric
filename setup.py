from setuptools import setup, find_packages

setup(
    name='my_django_setup',
    version='0.1',
    packages=find_packages(),
    install_requires=[
        'Django',
        # Other dependencies
    ],
    entry_points={
        'console_scripts': [
            'my-django-setup=my_django_setup.cli:main',
        ],
    },
)
