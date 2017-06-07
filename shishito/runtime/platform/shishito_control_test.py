import json
import os
import re

from shishito.runtime.shishito_support import ShishitoSupport


class ShishitoControlTest(object):
    """ Base class for ControlTest objects. """

    def __init__(self):
        self.shishito_support = ShishitoSupport()

        # create control environment object
        control_env_obj = self.shishito_support.get_module('test_environment')
        self.test_environment = control_env_obj(self.shishito_support)

        self.driver = None

    def start_browser(self):
        """ Webdriver startup function.

        :return: initialized webdriver
        """

        base_url = self.shishito_support.get_opt('base_url')
        config_section = self.shishito_support.get_opt('environment_configuration')

        # call browser from proper environment
        self.driver = self.test_environment.call_browser(config_section)

        # load init url
        if base_url:
            self.test_init(base_url)

        return self.driver

    def start_test(self, reload_page=None):
        """ To be executed before every test-case (test function).

        :param reload_page:
        """

    def stop_browser(self):
        """ Webdriver termination function. """

        self.driver.quit()
        del self.driver

    def stop_test(self, test_info, debug_events=None):
        """ To be executed after every test-case (test function). If test failed, function saves
        screenshots created during test.

        :param test_info: information about test
        """

        if test_info.test_status not in ('passed', None):
            # save screenshot in case test fails
            file_name = re.sub('[^A-Za-z0-9_. ]+', '', test_info.test_name)

            screenshot_folder = os.path.join(self.shishito_support.project_root, 'screenshots')

            if not os.path.exists(screenshot_folder):
                os.makedirs(screenshot_folder)

            self.driver.save_screenshot(os.path.join(screenshot_folder, file_name + '.png'))

            #Save debug info to file
            if debug_events is not None:
                debugevent_folder = os.path.join(self.shishito_support.project_root, 'debug_events')

                if not os.path.exists(debugevent_folder):
                    os.makedirs(debugevent_folder)

                with open(os.path.join(debugevent_folder, file_name + '.json'), 'w') as logfile:
                        json.dump(debug_events, logfile, indent=4)

    def test_init(self, url):
        """ Executed only once after browser starts.
         Suitable for general pre-test logic that do not need to run before every individual test-case.

        :param str url:
        """
