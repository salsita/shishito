Selenium Webdriver Python Project Templates
====================================================

Common template for all automated testing projects written with Selenium Webdriver & Python

## Test Project Structure

### Test Runner

* uses PyTest runner to execute test locally, or on custom combinations of Browser/OS/Resolution on BrowserStack.
* checks for available BrowserStack sessions and waits for one hour, if necessary (after that cancels test execution)
* archive the test results in .zip file

### Configuration files

#### > server_config.properties

* default configuration file with test variables
* changes to variables should be versioned in VCS; used for overnight/automated test execution

#### > local_config.properties

* if variable *local_execution=True*, script will look first into this local config for test variables
* in case variables are not found, it will fall back to values in default *server_config.properties* 
* changes to this file should **not** be kept in VCS (they server only for local test execution)

### Function Libraries
* common libraries with reusable functions
* configuration/helper functions + functions to be used directly within tests

### Page Objects
* template for page objects used by tests (see official selenium documentation for *Page Object Pattern* description)

### Tests
* template for selenium tests
* *conftest.py* - helper file that defines command line arguments for *pytest_runner.py* script

##How to use

### Typical Use
1. clone repository
* modify config files in */config* folder
* create some tests in */tests* folder
* run *pytest_runner.py* script

### Required Python Modules

* selenium (python selenium webdriver module)
* pytest (test runner)
* pytest-xdist (supports parallel test execution)
* pytest-instafail (shows test failures instantly - not at the end of the session)
* UnittestZero (provides better assertions than PyTest)

###Command line options

```
python pytest_runner.py --env [browserstack_environments] --tests [tests_to_run]

--env direct # runs on browserstack combinations passed to script through BROWSERSTACK environment variable (json)
--env versioned  # runs on browserstack combinations that are stored in "browserstack.properties" or "browserstack_smoke.properties" files

Note: see example below for BROWSERSTACK environment variable format sample

--tests smoke # runs only tests with fixture "@pytest.mark.smoke"
```

###Quick Start - Example

* clone repository
* add your BrowserStack credentials to *server_config.properties* (*bs_username*, *bs_password*)
* create sample Python file (on same directory level as *pytest_runner*) as below:

```python
import os

os.environ['BROWSERSTACK'] = '{"test_suite": [{"browser": "Firefox", "browser_version": "27.0", "os": "Windows",' \
                             ' "os_version": "7", "resolution": "1024x768"},' \
                             ' {"browser": "IE", "browser_version": "10.0", "os": "Windows",' \
                             ' "os_version": "7", "resolution": "1024x768"}]}'

# should run 2 tests on 3 BS combinations (versioned, all tests): 6
os.system('python pytest_runner.py')

# should run 2 tests on 2 BS combinations: 4
os.system('python pytest_runner.py --env direct')

# should run 2 tests on 3 BS combinations: 6
os.system('python pytest_runner.py --env versioned')

# should run 1 tests on 2 BS combinations: 2
os.system('python pytest_runner.py --env direct --tests smoke')

# should run 1 test on 1 BS combination: 1
os.system('python pytest_runner.py --env versioned --tests smoke')

# Total number of tests to be run: 19
```

- run the file
- you should see BrowserStack running tests for each os.system call

##Outstanding (to be done)
- correction of BrowserStack sessions status for test that failed (through API call)
- generate HTML report (so it can be picked up by Circle CI)
- more sophisticated way to handle BrowserStack collisions due to insufficiency of available sessions (currently script just waits for one hour) 