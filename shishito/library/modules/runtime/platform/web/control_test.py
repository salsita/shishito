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
from shishito.library.modules.runtime.environment.local.environment_control import EnvironmentControl
from shishito.library.modules.runtime.platform.web.control_execution import ControlExecution
from shishito.library.modules.runtime.shishito_support import ShishitoSupport


class ControlTest(object):
    def __init__(self):
        self.project_root = os.getcwd()
        # TODO load from pytest config
        self.environment_module = EnvironmentControl()
        self.platform_module = ControlExecution()
        self.driver = None
        self.config_file = os.path.join(self.project_root, 'config', self.platform_module.module_name,
                                        self.environment_module.module_name + '.properties')
        self.config = ConfigParser.RawConfigParser()
        self.shishito_support = ShishitoSupport()

    def get_default_browser_attributes(self, browser, height, url, width):
        """ Returns default browser values if not initially set """
        return (
            browser or self.shishito_support.gid('driver'),
            height or self.shishito_support.gid('window_height'),
            url or self.shishito_support.gid('base_url'),
            width or self.shishito_support.gid('window_width')
        )

    def start_browser(self, url=None, browser=None, width=None, height=None):
        """ Browser startup function.
         Initialize session over Browserstack or local browser. """
        # get default parameter values
        browser, height, url, width = self.get_default_browser_attributes(browser, height, url, width)

        self.environment_module.call_browser(browser_type=browser)
        self.driver.set_window_size(width, height)
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