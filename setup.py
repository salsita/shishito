from setuptools import find_packages, setup
from setuptools.command.install import install
import os
import sys

VERSION = '3.1.12'

with open('README.md', encoding='utf-8') as readme_file:
    readme = readme_file.read()

with open('HISTORY.md', encoding='utf-8') as history_file:
    history = history_file.read()

class VerifyVersionCommand(install):
    """Custom command to verify that the git tag matches our version"""
    description = 'verify that the git tag matches our version'

    def run(self):
        tag = os.getenv('CIRCLE_TAG')

        if tag != VERSION:
            info = "Git tag: {0} does not match the version of this app: {1}".format(
                tag, VERSION
            )
            sys.exit(info)


setup(
    name='shishito',
    version=VERSION,
    url='https://github.com/salsita/shishito',
    description='Python module for selenium webdriver test execution',
    long_description=readme + '\n\n' + history,
    long_description_content_type='text/markdown',
    author='Vojtech Burian',
    author_email='vojtech.burian@gmail.com',
    license='MIT',
    platforms='any',
    keywords=['testing', 'selenium', 'webdriver', 'browserstack', 'appium'],
    packages=find_packages(),
    package_data={
        'shishito': ['reporting/resources/*.js', 'reporting/resources/*.css', 'reporting/resources/*.html']
    },
    install_requires=[
        'selenium', 'pytest-xdist', 'pytest-instafail', 'pytest', 'UnittestZero',
        'Jinja2', 'requests', 'Appium-Python-Client', 'Click>=6.0'
    ],
    scripts=['shi'],
    entry_points={
        'console_scripts': [
            'shishito=shishito.cli:main',
        ],
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.5",
        "Topic :: Software Development :: Testing",
    ],
    cmdclass={
        'verify': VerifyVersionCommand,
    }
)
