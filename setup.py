from setuptools import find_packages, setup


long_description = """
shishito
========

Shishito is module for web application and browser extension integration testing
with Selenium Webdriver & Python. It runs tests using included libraries and
generates nice test results output.
"""


setup(
    name='shishito',
    version='3.0.0',
    url='https://github.com/salsita/shishito',
    description='Python module for selenium webdriver test execution',
    long_description=long_description,
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
        'Jinja2', 'requests', 'Appium-Python-Client'
    ],
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
)
