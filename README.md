# Shishito

Shishito is module for web application and browser extension integration testing with Selenium Webdriver & Python.
It runs tests using included libraries and generates nice test results output.

## Features

* runs python Selenium Webdriver tests via PyTest
* easy configuration for local and remote (BrowserStack, Remote Driver) test execution
* support browser extensions testing through Selenium
* contains useful test libraries
* generates HTML test results report (with screenshots for failed tests)
* designed to be used as a module (by multiple projects if needed)

## Pre-requisities

Install Python moodules from requirements.txt

```pip install -r requirements.txt```

To build Chrome extension from sources automatically

* crxmake

```
sudo apt-get install swig
sudo pip install crxmake
```

Webdriver drivers need to be setup (ChromeDriver, InternetExplorerDriver etc.)

## Quick Start

1. clone Shishito repository.
```git clone git@github.com:salsita/shishito.git```
1. add *salsa_webqa* directory into PYTHONPATH environment variable
1. clone sample test project repository https://github.com/salsita/shishito-sample-project
```git clone git@github.com:salsita/shishito-sample-project.git```
1. if you want to use BrowserStack for running your tests, replace "bs_username", "bs_password" values with your credentials in ***shishito-sample-project/config/server_config.properties***
 or pass it to runner python file as command line argument using flag --browserstack username:token
1. install Firefox or change "driver" value to some other installed driver in ***shishito-sample-project/config/local_config.properties***
Available values  "BrowserStack", "Firefox", "Chrome", "IE", "PhantomJS", "Opera".
1. run *google_test_runner.py* in sample project folder!

If you use local driver, you should now observe browser being started and tests running.
There are information about progress shown in console output.
Once testing is finished, HTML report can be found in:
```
shishito-sample-project/results folder # HTML report
shishito-sample-project/results_archive folder # zipped HTML report
```

## Continuous Integration

Using Shishito with Continuous Integration solution, such as Jenkins, is easy!
All you need to do is clone Shishito repo and add it into the PYTHONPATH.

Example script below (Jenkins "execute shell" build step):
```bash
#!/bin/bash
######################
# clone Shishito  #
######################

cd $WORKSPACE
git clone git@github.com:salsita/shishito.git

######################
# VARIABLES          #
######################

export PYTHONPATH=${PYTHONPATH}:/$WORKSPACE/shishito

######################
# SCRIPT             #
######################

python google_test_runner.py
```

## Command line options

```python
python custom_runner.py --env [browserstack_environments] --tests [tests_to_run] --browserstack [username:token]

--env direct # runs tests on browserstack combinations
             # passed to script through BROWSERSTACK environment variable (json)

os.environ['BROWSERSTACK'] = '{"test_suite": [{"browser": "Firefox", "browser_version": "27.0",
                             ' "os": "Windows", "os_version": "7", "resolution": "1024x768"},' \
                             ' {"browser": "IE", "browser_version": "10.0", "os": "Windows",' \
                             ' "os_version": "7", "resolution": "1024x768"}]}'

--env versioned  # runs on browserstack combinations that are stored in "browserstack.properties"
                 # or "browserstack_smoke.properties" files

--tests smoke # runs only tests with fixture "@pytest.mark.smoke", only for desctop
--mobile yes # run tests on mobile browserstack combinations that are stored in "browserstack_mobile.properties" - can't be at the same time with smoke, default value is none

--browserstack testuser1:p84asd21d15asd454 # authenticate on BrowserStack using user "testuser1" and token "p84asd21d15asd454"
--reporting all # generate reports for selenium and non selenium tests, if you want to run only selenium use value "selenium", for non selenium use "simple"

```

Combinations yet unsupported by Shishito:
* `--mobile yes` together with `--tests smoke`
* `--env direct` together with `--tests smoke`

If no arguments are specified, Shishito, by default, searches for BROWSERSTACK combinations in .properties files and runs all tests
##Run different tests types (selenium and non selenium)
* to do this use command line parameter: --reporting, default option is "all", other options are "selenium" and "simple"
* to run non selenium tests with runner: create folder "non_selenium_tests" and put there tests and conftest.py files, if project contain only non selenium tests, then in command line parameter provide --reporting simple

## Configuration

***server_config.properties***

* default configuration file with test variables
* changes to variables should be maintained in VCS; so that configuration can be reused for automated test execution

```
# General
base_url=http://www.google.com
driver=Firefox

# Remote driver
remote_hub=http://localhost:4444/wd/hub
browser_version=34.0
platform=WINDOWS
```

* *base_url* - url that will be loaded by default upon start of each test
* *driver* - name of driver used. For Browserstack use "BrowserStack"
* *remote_hub* - remote driver hub. If specified & BrowserStack is not used, tests will be run on remote driver (not on local browsers)
* *browser_version* - version of browser. Used for remote driver (Selenium Grid, not Browserstack)
* *platform* - OS platform. Used for remote driver (Selenium Grid, not Browserstack)

***local_config.properties***

* if variable *local_execution=True*, script will look first search local config for test variables
* in case variables are not found, it will fall back to values in default *server_config.properties*
* changes to this file should **not** be maintained in VCS (they serve only for local test execution)

* *conftest.py* - helper file that defines command line arguments, provides fixtures and other information for Shishito runner

***browserstack.properties & browserstack_smoke.properties***

* contains BrowserStack combinations tests should run on
* only used if *driver=BrowserStack* in *local_config.properties* or *server_config.properties*
* default file is *browserstack.properties*; *browserstack_smoke.properties* is used when argument *--tests smoke* is passed to Shishito runner

## Browser Extensions

Browser Extensions can be automatically installed before testing using Chrome or Firefox.
This works on BrowserStack cloud as well.

In order to automatically install browser extensions into browsers, "with_extension" property (from *local_config.properties* and/or *server_config.properties*) needs to be set to *true*.
When folder 'extension' is available in project root, Shishito will then install any extension in this folder before testing (for appropriate browser).

"path_to_extension_code" is optional, but once it is filled with path to extension source code folder (relative to test project root folder), Shishito will automatically build .crx file from source code, using crxmake https://github.com/bellbind/crxmake-python, and install this extension. Building extension from source option is available only for Chrome browser now.
```
# Extension settings
with_extension=true
path_to_extension_code=../test-extension/source/main
```
