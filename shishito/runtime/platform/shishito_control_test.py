import os
import re

from shishito.runtime.shishito_support import ShishitoSupport


class ShishitoControlTest(object):

    def __init__(self):
        self.shishito_support = ShishitoSupport()

        # create control environment object
        control_env_obj = self.shishito_support.get_modules('test_environment')
        self.test_environment = control_env_obj(self.shishito_support)

        self.driver = None

    def start_browser(self):
        """ Browser startup function.
         Initialize session over Browserstack or local browser. """

        base_url = self.shishito_support.get_opt('base_url')
        config_section = self.shishito_support.get_opt('environment_configuration')

        # call browser from proper environment
        self.driver = self.test_environment.call_browser(config_section)

        # load init url
        if base_url:
            self.test_init(base_url)

        return self.driver

    def start_test(self, reload_page=None):
        """ To be executed before every test-case (test function) """

    def stop_browser(self):
        """ Browser termination function """

        self.driver.quit()

    def stop_test(self, test_info):
        """ To be executed after every test-case (test function) """
        if test_info.test_status not in ('passed', None):
            # save screenshot in case test fails
            screenshot_folder = os.path.join(self.shishito_support.project_root, 'screenshots')
            if not os.path.exists(screenshot_folder):
                os.makedirs(screenshot_folder)

            file_name = re.sub('[^A-Za-z0-9_. ]+', '', test_info.test_name)
            self.driver.save_screenshot(os.path.join(screenshot_folder, file_name + '.png'))

    def test_init(self, url):
        """ Executed only once after browser starts.
         Suitable for general pre-test logic that do not need to run before every individual test-case. """
