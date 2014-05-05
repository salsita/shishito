# Salsa WebQA

Salsa WebQA is test module for integration testing with Selenium Webdriver & Python.
It runs tests using included libraries and generates nice test results output.

## Features

* runs python Selenium Webdriver tests via PyTest
* easy configuration for local and remote (BrowserStack) test execution
* contains useful test libraries
* generates HTML test results report (with screenshots for failed tests)
* designed to be used as a module (by multiple projects if needed)

## Pre-requisities

Following python modules needs to be installed

* selenium
* pytest
* pytest-xdist
* pytest-instafail
* UnittestZero

```pip install selenium pytest pytest-xdist pytest-instafail UnittestZero```
*(On linux run as root with 'sudo')*

Webdriver drivers need to be setup (ChromeDriver, InternetExplorerDriver etc.)

## Quick Start

1. clone Salsa WebQA repository.
```git clone git@github.com:salsita/salsa-webqa.git```
1. add *salsa_webqa* directory into PYTHONPATH environment variable
1. clone sample test project repository https://github.com/salsita/salsa-webqa-sample-project
```git clone git@github.com:salsita/salsa-webqa-sample-project.git```
1. if you want to use BrowserStack for running your tests, replace "bs_username", "bs_password" values with your credentials in ```salsa-webqa-sample-project/config/server_config.properties```
1. install Firefox or change "driver" value to some other installed driver in
```salsa-webqa-sample-project/config/local_config.properties```
Available values  "BrowserStack", "Firefox", "Chrome", "IE", "PhantomJS", "Opera"
1. run *google_test_runner.py* in sample project folder!

If you use local driver, you should now observe browser being started and tests running.
There are information about progress shown in console output.
Once testing is finished, HTML report can be found in:
```
salsa-webqa-sample-project/results folder # HTML report
salsa-webqa-sample-project/results_archive folder # zipped HTML report
```

## Continuous Integration

Using Salsa WebQA with Continuous Integration solution, such as Jenkins, is easy!
All you need to do is clone Salsa WebQA repo and add it into the PYTHONPATH.

Example script below (Jenkins "execute shell" build step):
```bash
#!/bin/bash
######################
# clone Salsa WebQA  #
######################

cd $WORKSPACE
git clone git@github.com:salsita/salsa-webqa.git

######################
# VARIABLES          #
######################

export PYTHONPATH=${PYTHONPATH}:/$WORKSPACE/salsa-webqa

######################
# SCRIPT             #
######################

python google_test_runner.py
```

## Command line options

```python
python custom_runner.py --env [browserstack_environments] --tests [tests_to_run]

--env direct # runs tests on browserstack combinations
             # passed to script through BROWSERSTACK environment variable (json)

os.environ['BROWSERSTACK'] = '{"test_suite": [{"browser": "Firefox", "browser_version": "27.0",
                             ' "os": "Windows", "os_version": "7", "resolution": "1024x768"},' \
                             ' {"browser": "IE", "browser_version": "10.0", "os": "Windows",' \
                             ' "os_version": "7", "resolution": "1024x768"}]}'

--env versioned  # runs on browserstack combinations that are stored in "browserstack.properties"
                 # or "browserstack_smoke.properties" files

--tests smoke # runs only tests with fixture "@pytest.mark.smoke"
```

If no arguments are specified, Salsa WebQA, by default, searches for BROWSERSTACK combinations in .properties files and runs all tests

## Configuration

***server_config.properties***

* default configuration file with test variables
* changes to variables should be maintained in VCS; so that configuration can be reused for automated test execution

***local_config.properties***

* if variable *local_execution=True*, script will look first search local config for test variables
* in case variables are not found, it will fall back to values in default *server_config.properties*
* changes to this file should **not** be maintained in VCS (they serve only for local test execution)

* *conftest.py* - helper file that defines command line arguments, provides fixtures and other information for salsa_webqa runner

***browserstack.properties & browserstack_smoke.properties***

* contains BrowserStack combinations tests should run on
* only used if *driver=BrowserStack* in *local_config.properties* or *server_config.properties*
* default file is *browserstack.properties*; *browserstack_smoke.properties* is used when argument *--tests smoke* is passed to salsa_webqa runner
