from shishito.runtime.platform.shishito_control_test import ShishitoControlTest


class ControlTest(ShishitoControlTest):
    """ ControlTest for generic platform """

    def start_browser(self):
        """ Webdriver startup function.

        :return: initialized webdriver
        """

    def start_test(self, reload_page=None):
        """ To be executed before every test-case (test function).

        :param reload_page:
        """

    def stop_browser(self):
        """ Webdriver termination function. """

    def stop_test(self, test_info):
        """ To be executed after every test-case (test function). If test failed, function saves
        screenshots created during test.

        :param test_info: information about test
        """
