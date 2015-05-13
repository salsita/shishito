# /usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: Vojtech Burian
@summary: Common configuration functions supporting test execution.
 Various startup and termination procedures, helper functions etc.
 Not to be used for directly testing the system under test (must not contain Asserts etc.)
"""

import os
import time
import re

from shishito.library.modules.runtime.shishito_support import ShishitoSupport


class ControlTest(object):

    def __init__(self):
        # TODO: os.getcwd() may not always work (if runner is not used)
        self.project_root = os.getcwd()

        self.shishito_support = ShishitoSupport()

        # create control environment object
        control_env_obj = self.shishito_support.get_modules(module='test_environment')
        self.test_environment = control_env_obj(self.shishito_support)

        self.driver = None

    def start_browser(self):
        """ Browser startup function.
         Initialize session over Browserstack or local browser. """

        base_url = self.shishito_support.gid('base_url')
        combination = self.shishito_support.gid('environment_configuration')

        # call browser from proper environment
        self.driver = self.test_environment.call_browser(combination)

        # set_window_size moved to call_browser

        # load init url
        if base_url:
            self.test_init(base_url)

        return self.driver

    def stop_browser(self, delete_cookies=True):
        """ Browser termination function """

        if delete_cookies:
            self.driver.delete_all_cookies()

        self.driver.quit()

    def test_init(self, url):
        """ Executed only once after browser starts.
         Suitable for general pre-test logic that do not need to run before every individual test-case. """

        self.driver.get(url)
        self.driver.implicitly_wait(int(self.shishito_support.gid('default_implicit_wait')))

    def start_test(self, reload_page=None):
        """ To be executed before every test-case (test function) """

        if reload_page:
            self.driver.get(self.shishito_support.gid('base_url'))
            self.driver.implicitly_wait(self.shishito_support.gid('default_implicit_wait'))
            time.sleep(5)

    def stop_test(self, test_info):
        """ To be executed after every test-case (test function) """
        if test_info.test_status not in ('passed', None):
            # save screenshot in case test fails
            screenshot_folder = os.path.join(self.project_root, 'screenshots')
            if not os.path.exists(screenshot_folder):
                os.makedirs(screenshot_folder)

            file_name = re.sub('[^A-Za-z0-9_. ]+', '', test_info.test_name)
            self.driver.save_screenshot(os.path.join(screenshot_folder, file_name + '.png'))
