"""
@author: Vojtech Burian
@summary: Common configuration functions supporting test execution.
Various startup and termination procedures, helper functions etc.
Not to be used for directly testing the system under test (must not contain Asserts etc.)
"""

import time

from shishito.runtime.platform.shishito_control_test import ShishitoControlTest


class ControlTest(ShishitoControlTest):
    """ ControlTest for web platform """

    def stop_browser(self, delete_cookies=True):
        """ Webdriver termination function.

        :param bool delete_cookies: delete cookies from webdriver
        """

        if delete_cookies:
            self.driver.delete_all_cookies()

        self.driver.quit()

    def test_init(self, url):
        """ Executed only once after browser starts.
        Suitable for general pre-test logic that do not need to run before every individual test-case.
        Open given url and wait for given time (setting "default_implicit_wait").

        :param str url: url which should be opened
        """

        self.driver.get(url)
        self.driver.implicitly_wait(int(self.shishito_support.get_opt('default_implicit_wait')))

    def start_test(self, reload_page=None):
        """ To be executed before every test-case (test function).

        :param reload_page: it True reloads page and waits
        """

        if reload_page:
            self.driver.get(self.shishito_support.get_opt('base_url'))
            self.driver.implicitly_wait(self.shishito_support.get_opt('default_implicit_wait'))
            time.sleep(5)
