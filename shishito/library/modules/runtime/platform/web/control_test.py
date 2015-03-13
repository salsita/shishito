# /usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: Vojtech Burian
@summary: Common configuration functions supporting test execution.
 Various startup and termination procedures, helper functions etc.
 Not to be used for directly testing the system under test (must not contain Asserts etc.)
"""
import ConfigParser
import os
import time
import re

# from salsa_webqa.library.support.jira_zephyr_api import ZAPI
from shishito.library.modules.runtime.shishito_support import ShishitoSupport


class ControlTest(object):
    def __init__(self):
        # TODO os.getcwd() may not always work (if runner is not used)
        self.project_root = os.getcwd()
        self.shishito_support = ShishitoSupport()
        self.platform_name = self.shishito_support.gid('test_platform')
        self.environment_name = self.shishito_support.gid('test_environment')
        self.modules = self.shishito_support.get_modules(self.platform_name, self.environment_name)
        self.driver = None

        # load config file
        self.config_file = os.path.join(self.project_root, 'config', self.platform_name,
                                        self.environment_name + '.properties')
        self.config = ConfigParser.RawConfigParser()

    # def get_default_browser_attributes(self, browser, height, url, width):
    # """ Returns default browser values if not initially set """
    #     # TODO remove this probably in favor of .properties file
    #     return (
    #         browser or self.shishito_support.gid('driver').lower(),
    #         height or self.shishito_support.gid('window_height').lower(),
    #         url or self.shishito_support.gid('base_url').lower(),
    #         width or self.shishito_support.gid('window_width').lower()
    #     )

    def start_browser(self):
        """ Browser startup function.
         Initialize session over Browserstack or local browser. """
        # get default parameter values
        # browser, height, url, width = self.get_default_browser_attributes(browser, height, url, width)
        # TODO pass combination (config section) from pytest argument OR environment .properties file (if runner not used)
        # self.shishito_support.gid('environment_configuration')
        combination = 'Chrome'

        self.driver = self.modules['test_environment']().call_browser(combination=combination)
        # self.driver.set_window_size(width, height)
        url = self.shishito_support.gid('base_url')
        if url:
            self.test_init(url)
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