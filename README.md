Integration Testing Support
====================

This is where common or reusable test code goes.

Example how to use pytest_runner: (more detailed guide to follow soon..)

- clone repo
- add your BrowserStack credentials to *server_config.properties* (*bs_username*, *bs_password*)
- create Python file as below:

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
- you should see BrowserStack running tests for each os.system call. Number of expected tests to be run is in the script