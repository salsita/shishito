"""
@summary: Common configuration functions supporting test execution.
 Various startup and termination procedures, helper functions etc.
 Not to be used for directly testing the system under test (must not contain Asserts etc.)
"""
import os
import re
from shishito.runtime.platform.shishito_control_test import ShishitoControlTest
#import pyscreenshot as Screenshotter


class ControlTest(ShishitoControlTest):
    """ ControlTest for node-webkit platform """

    def start_browser(self):
        # call browser from proper environment
        config_section = self.shishito_support.get_opt('environment_configuration')
        print("*********** config_section =", config_section)
        self.driver = self.test_environment.call_browser(config_section)
        return self.driver

    def test_init(self):
        """ Executed only once after browser starts.
        Suitable for general pre-test logic that do not need to run before every individual test-case.
        Waiting for given time (setting "default_implicit_wait").
        """
        self.driver.implicitly_wait(int(self.shishito_support.get_opt('default_implicit_wait')))


    def stop_test(self, test_info):
        """
        !!!TEMPORARY METHOD!!! \n
        To be executed after every test-case (test function). If test failed, function saves
        screenshots created during test.

        For more information see: https://code.google.com/p/chromedriver/issues/detail?id=816

        :param test_info: information about test
        :return:
        """
        if test_info.test_status not in ('passed', None):
            # save screenshot in case test fails
            screenshot_folder = os.path.join(self.shishito_support.project_root, 'screenshots')

            if not os.path.exists(screenshot_folder):
                os.makedirs(screenshot_folder)

            file_name = re.sub('[^A-Za-z0-9_. ]+', '', test_info.test_name)
            self.driver.save_screenshot(os.path.join(screenshot_folder, file_name + '.png'))
            #Screenshotter.grab_to_file(os.path.join(screenshot_folder, file_name + '.png'))
