.. Shishito documentation master file, created by
   sphinx-quickstart on Fri May 22 12:26:43 2015.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Shishito
========

Shishito is module for web application and browser extension integration testing with Selenium Webdriver & Python.
It runs tests using included libraries and generates nice test results output.

Features
========

    * runs python Selenium Webdriver tests via PyTest
    * easy configuration for local and remote (BrowserStack, Appium, ..) test execution
    * contains useful test libraries
    * generates HTML test results report (with screenshots for failed tests)
    * designed to be used as a module (by multiple projects if needed)

Package structure
=================

  * conf

    * Configuration file for PyTest (conftest.py). Module adds custom argument to PyTest runner and define functions that can modify pytest behaviour.
      This file should be imported from each test directory conftest.py file.

  * reporting

    * Module is responsible for creating test results reports. Module offers function for handling test results (archive results, clean results, ..).
      Templates for test results are stored in this module.


Contents
========

.. toctree::
   :maxdepth: 2

   modules


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

