# Shishito

Shishito is module for web and mobile application functional testing using Selenium Webdriver & Python.
It runs tests using included libraries and generates nice test results output.

Documentation - http://shishito.readthedocs.org/en/latest/index.html (hosted on Read the Docs)

## Features

* runs python Selenium Webdriver tests via PyTest
* easy configuration for local and remote (BrowserStack, Appium, ..) test execution
* contains useful test libraries
* generates HTML test results report (with screenshots for failed tests)
* designed to be used as a module (by multiple projects if needed)

## Pre-requisities

Install Python moodules from requirements.txt

```pip install -r requirements.txt```

Webdriver drivers need to be setup (ChromeDriver, InternetExplorerDriver etc.)

## Quick Start

1. clone Shishito repository.
```git clone git@github.com:salsita/shishito.git```
1. add *shishito* directory into PYTHONPATH environment variable
1. clone sample test project repository https://github.com/salsita/shishito-sample-project
```git clone git@github.com:salsita/shishito-sample-project.git```
1. if you want to use BrowserStack for running your tests, replace "bs_username", "bs_password" values with your credentials in ***shishito-sample-project/config/server_config.properties***
 or pass it to runner python file as command line argument using flag --browserstack username:token
1. if you want to use Saucelabs for running your tests, add your credentials to saucelabs variable in ***shishito-sample-project/config/server_config.properties***
 or pass it to runner python file as command line argument using flag --saucelabs username:token
1. set your preferred browser settings in ***shishito-sample-project/config/web/(browserstack|local).properties*** or for mobile apps in ***shishito-sample-project/config/mobile/appium.properties***
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
--platform web         # define platform on which run tests (currently supported: web, mobile, generic)
--environmnet local    # define environment in which run tests (currently supported: local, browserstack, appium, remote)
--test_directory tests # define directory where to lookup for tests (project_root + test_directory)

# supported platform/environment combinations:
#   generic/local
#   generic/remote
#   web/local
#   web/browserstack
#   web/remote
#   mobile/appium (can run on local/remote appium server or on saucelabs)
#   node_webkit/node_webkit

--smoke # runs only tests with fixture "@pytest.mark.smoke"

--browserstack testuser1:p84asd21d15asd454 # authenticate on BrowserStack using user "testuser1" and token "p84asd21d15asd454"
--saucelabs testuser1:p84asd21d15asd454 # authenticate on Saucelabs using user "testuser1" and token "p84asd21d15asd454"
--test_rail user@email.com:1AVFS51AS # authenticate on TestRail using user email "user@email.com" and password "1AVFS51AS"

```

If no arguments are specified, Shishito, by default, searches for settings combinations in (server|local).properties files and runs tests according to them.

## Configuration files

***server_config.properties***

* default configuration file with test variables
* changes to variables should be maintained in VCS; so that configuration can be reused for automated test execution

```
# modules
test_platform=web
test_environment=local

# test dir
test_directory=tests

# General
base_url=http://www.google.com
environment_configuration=Chrome
```

* *test_platform* - on which platform run tests (web, mobile)
* *test_environment* - in which environment run tests (local, browserstack, appium)
* *test_directory* - in which directory lookup for tests
* *base_url* - url that will be loaded by default upon start of each test
* *environment_configuration* - which configuration use from <environment>.properties file (used when tests are run without runner)
* *remote_driver_url* - remote driver hub. Selenium server needs to be running on this url.

***local_config.properties***

* if variable *local_execution=True*, script will look first search local config for test variables
* in case variables are not found, it will fall back to values in default *server_config.properties*
* changes to this file should **not** be maintained in VCS (they serve only for local test execution)

***\<platform\>/\<environment\>.properties***

* contains combinations, for which the tests should be executed
* e.g. browser and resolution for local web browser

***conftest.py***

* helper file that defines command line arguments, provides fixtures and other information for Shishito runner

## Configuration

Shishito can be configured with command lines arguments and config files. Some configuration values are also added as arguments to PyTest (depends on test environment).
Configuration values are looked up according to these priorities:
1. pytest.config
1. command line arguments
1. local configuration file (if enabled: local_execution=True)
1. server cofiguration file

### Node-webkit configuration
Shishito is able to run tests against node-webkit applications. Current implementation does not allow tester to specify based URL, just to run application from URL directly specified within application.
Creating of webdriver driver object is done by specific [chromedriver](https://github.com/nwjs/nw.js/wiki/Chromedriver) which has to be placed in same directory as node-webkit application. 
Chromedriver will search for node-webkit binaries and start the application. Binaries have to have specific names otherwise chromedriver won't find them.  
Node-webkit binary must have name:

* For Linux: `nw`
* For Windows: `nw.exe`
* For OS X: `node-webkit.app`

#### TEMPORARY SCREENSHOT ON FAILURE FUNCTIONALITY
Due to [issue in Node-webkit chromedriver](https://code.google.com/p/chromedriver/issues/detail?id=816); there is added 
temporary screenshot on failure functionality using [pyscreenshot module](https://pypi.python.org/pypi/pyscreenshot). This functionality takes screenshot of whole desktop not only node-webkit 
application window. This issue should be fixed in chromedriver 2.15. There is alpha version of node-webkit chromedriver v2.15.
This functionality is going to be removed once issue is fixed.

**Note**: Ubuntu: It is necessary to install also python-imaging
 `sudo apt-get install python-imaging`

#### Troubleshooting for Node-webkit platform
If you see exception similar to one below

```
   raise WebDriverException(
       \"\'\" + os.path.basename(self.path) + \"\' executable needs to be \
           available in the path. Please look at \
           http://docs.seleniumhq.org/download/#thirdPartyDrivers \
           and read up at \
\>                   http://code.google.com/p/selenium/wiki/ChromeDriver")
E    WebDriverException: Message: 'chromedriver' executable needs to be available in the path. Please look at http://docs.seleniumhq.org/download/#thirdPartyDrivers and read up at http://code.google.com/p/selenium/wiki/ChromeDriver

/usr/local/lib/python2.7/dist-packages/selenium/webdriver/chrome/service.py:70: WebDriverException
```
You need to check Chromedriver file access rights mainly in Linux or OS X, Windows should be ok. 
## Test Management Support

Shishito support upload of test results to TestRail test management app.
Following properties in server/local config have to be filled:

* *test_rail* - credentials for test rail. Can be also left empty and passed via cmd argument (see above)
* *test_rail_url* - URL of test rail instance. (example: https://mycompany.testrail.net)
* *test_rail_project_id* - ID of TestRail project (example: 1)
* *test_rail_section_id* - ID of TestRail test section (example: 2)
* *test_rail_test_plan_id* - ID of TestRail test plan (example: 5)
* *test_rail_suite_id* - ID of TestRail test suite (example: 1)

For further information, see TestRail API documentation http://docs.gurock.com/testrail-api2/start.