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

Package overview
=================

  * :doc:`conf <shishito.conf>`

    * Configuration file for PyTest (*conftest.py*). Module adds custom arguments to PyTest runner and defines functions that can modify pytest behaviour.
      Contents of this file should be imported from each test directory conftest.py file.

    ::

        from shishito.conf.conftest import *

  * :doc:`reporting <shishito.reporting>`

    * Module is responsible for creating test results reports. Module offers functions for handling test results (archive results, clean results, ..).
      Templates for test results are stored in this module.

  * :doc:`runtime <shishito.runtime>`

    * Module contains submodules needed for running test in given environment and platform. Module also contains support class (*ShishitoSupport*), used for loading
      config files (*load_configs*, *get_environment_config*), importing platform and environment specific classes (*get_module*) and getting settings from configuration (*get_opt*).

    * :doc:`environment <shishito.runtime.environment>`

      * Module contains environment specific classes (*ControlEnvironment*) and base class for all environment (*ShishitoEnvironment*). *ControlEnvironment* class
        offers following functionality:

        * (*get_pytest_arguments*) Return environment specific arguments for PyTest runner
        * (*call_browser*) Create selenium driver for specific environment

      * Module offers support for following environments: **appium**, **browserstack**, **local** and **remote**.

        * **apium** is used for running tests for mobile applications
        * **broserstack** is used for running tests on specific OS and browser combination (offered by browserstack)
        * **local** is used for running tests on local browsers
        * **remote** is used for running tests on remote browsers

    * :doc:`platform <shishito.runtime.platform>`

      * Module contains base classes for platform specific functionality and submodules for supported platforms.
      * Module contains followig base classes:

        * *ShishitoExecution* - execute PyTest with correct arguments for specific platform. Class offers following functionality:

          * (*run_tests*) Execute tests for all specified combinations in config file ("config/<platform>/<environment>.properties")
          * (*trigger_pytest*) Set up PyTest runner and execute it

        * *ShishitoControlTest* - contain functions used in tests (initialize selenium driver, store test results, ..). Class offers following functionality:

          * (*start_browser*) Prepare webdriver used in tests. Should be used in *setup_class* method.
          * (*start_test*) Initialize webdriver before every test function execution (e.g. load initial page). Should be used in *setup_method* method.
          * (*stop_browser*) Terminate webdriver. Should be used in *teardown_class* method.
          * (*stop_test*) Handle one test function results (e.g. save screenshots in case of test fail). Should be used in *teardown_method* method.

      * Shishito supports following platforms: **generic**, **mobile** and **web**.

        * **generic** platform is used for running tests, that do not require selenium webdriver
        * **mobile** platform is used for running tests, that test mobile applications using appium or saucelabs (using appium webdriver)
        * **web** platform is used for running tests, that use local/remote browsers or browserstack (using selenium webdriver)
        * Each platform implements two classes: *ControlExecution* (bases *ShishitoExecution*) and *ControlTest* (bases *ShishitoControlTest*)


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

