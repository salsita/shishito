import json
import os
import re

from shishito.runtime.shishito_support import ShishitoSupport
from shishito.ui.selenium_support import SeleniumTest


class ShishitoControlTest(object):
    """ Base class for ControlTest objects. """

    def __init__(self):
        self.shishito_support = ShishitoSupport()

        # create control environment object
        control_env_obj = self.shishito_support.get_module('test_environment')
        self.test_environment = control_env_obj(self.shishito_support)

        self.drivers = []

    def start_browser(self, base_url = None):
        """ Webdriver startup function.

        :return: initialized webdriver
        """

        config_section = self.shishito_support.get_opt('environment_configuration')

        # call browser from proper environment
        driver = self.test_environment.call_browser(config_section)
        self.drivers.append(driver)

        # load init url
        if not base_url:
            base_url = self.shishito_support.get_opt('base_url')

        if base_url:
            self.test_init(driver, base_url)
        else:
            self.test_init(driver)
        return driver

    def start_test(self, reload_page=None):
        """ To be executed before every test-case (test function).

        :param reload_page:
        """

    def stop_browser(self):
        """ Webdriver termination function. """

        for driver in self.drivers:
            driver.quit()   # Cleanup the driver info
        del self.drivers[:]

    def stop_test(self, test_info, debug_events=None):
        """ To be executed after every test-case (test function). If test failed, function saves
        screenshots created during test.

        :param test_info: information about test
        """

        if test_info.test_status not in ('passed', None):
            # save screenshot in case test fails
            test_name = re.sub('[^A-Za-z0-9_.]+', '_', test_info.test_name)

            # Capture screenshot and debug info from driver(s)
            for driver in self.drivers:
                if(self.shishito_support.test_platform == 'mobile'):
                    browser_name = 'appium'
                else:
                    browser_name = driver.name
                file_name = browser_name + '_' + test_name
                ts = SeleniumTest(driver)
                ts.save_screenshot(name=file_name)

                #Save debug info to file
                if debug_events is not None:
                    debugevent_folder = os.path.join(self.shishito_support.project_root, 'debug_events')

                    if not os.path.exists(debugevent_folder):
                        os.makedirs(debugevent_folder)

                    with open(os.path.join(debugevent_folder, file_name + '.json'), 'w') as logfile:
                            json.dump(debug_events, logfile)

    def test_init(self, driver, url=None):
        """ Executed only once after browser starts.
         Suitable for general pre-test logic that do not need to run before every individual test-case.

        :param WebDriver driver: driver instance to set up
        :param str url: initial URL

        """
