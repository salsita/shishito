"""
@summary: Common configuration functions supporting test execution.
 Various startup and termination procedures, helper functions etc.
 Not to be used for directly testing the system under test (must not contain Asserts etc.)
"""

from shishito.runtime.platform.shishito_control_test import ShishitoControlTest



class ControlTest(ShishitoControlTest):
    """ ControlTest for mobile platform """
    def test_init(self, url):
        """ Executed only once after browser starts.
         Suitable for general pre-test logic that do not need to run before every individual test-case.

        :param str url:
        """
        test_platform = self.shishito_support.test_platform
        test_env = self.shishito_support.get_opt('test_environment')
        if(test_env == 'browserstack' and test_platform == 'mobile'):
            self.driver.get(url)
            self.driver.implicitly_wait(int(self.shishito_support.get_opt('default_implicit_wait')))


