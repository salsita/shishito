# /usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: Vojtech Burian
@summary: Common configuration functions supporting test execution.
 Various startup and termination procedures, helper functions etc.
 Not to be used for directly testing the system under test (must not contain Asserts etc.)
"""

# from salsa_webqa.library.support.jira_zephyr_api import ZAPI


class ShishitoControlTest(object):
    def __init__(self):
        pass

    def get_default_browser_attributes(self, browser, height, url, width):
        """ Returns default browser values if not initially set """
        pass

    def start_browser(self, url=None, browser=None, width=None, height=None):
        """ Browser startup function.
         Initialize session over Browserstack or local browser. """
        pass

    def stop_browser(self, delete_cookies=True):
        """ Browser termination function """
        pass

    def test_init(self, url):
        """ Executed only once after browser starts.
         Suitable for general pre-test logic that do not need to run before every individual test-case. """
        pass

    def start_test(self, reload_page=None):
        """ To be executed before every test-case (test function) """
        pass

    def stop_test(self, test_info):
        """ To be executed after every test-case (test function) """
        pass