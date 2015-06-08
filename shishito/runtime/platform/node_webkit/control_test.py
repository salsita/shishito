"""
@summary: Common configuration functions supporting test execution.
 Various startup and termination procedures, helper functions etc.
 Not to be used for directly testing the system under test (must not contain Asserts etc.)
"""

from shishito.runtime.platform.shishito_control_test import ShishitoControlTest


class ControlTest(ShishitoControlTest):
    """ ControlTest for node-webkit platform """

    def start_browser(self):
        # call browser from proper environment
        self.driver = self.test_environment.call_browser('')

        return self.driver

    def test_init(self):
        """ Executed only once after browser starts.
        Suitable for general pre-test logic that do not need to run before every individual test-case.
        Waiting for given time (setting "default_implicit_wait").
        """
        self.driver.implicitly_wait(int(self.shishito_support.get_opt('default_implicit_wait')))

    def stop_browser(self):
        # closing browser (node-webkit application) once tests are finished
        self.driver.quit()
