import inspect
import os
import re
from selenium import webdriver


class ShishitoEnvironment(object):
    """ Base class for test environment. """

    def __init__(self, shishito_support):
        self.shishito_support = shishito_support

    def add_extension_to_browser(self, browser_profile, crx_path):
        """ Return browser profile updated with one or more extensions """
        crx_paths = crx_path.split('|')
        for chr_extension in crx_paths:
            browser_profile.add_extension(os.path.join(self.shishito_support.project_root, 'extension', chr_extension))

        return browser_profile

    def call_browser(self, config_section):
        """ Start webdriver for given config section. Prepare capabilities for the browser, set browser resolution.

        :param str config_section: section in platform/environment.properties config
        :return: created webdriver
        """

        # get browser capabilities
        print(config_section)
        capabilities = self.get_capabilities(config_section)
        profile = self.get_browser_profile(config_section.lower(), capabilities)

        # get browser type
        browser_type = self.shishito_support.get_opt(config_section, 'browser')
        browser_type = browser_type.lower()

        # get driver
        driver = self.start_driver(browser_type, capabilities)

        # set browser size is defined
        browser_size = self.shishito_support.get_opt(config_section, 'resolution')
        if browser_size:
            # default size --> leave it on webdriver
            width, height = browser_size.split('x')
            driver.set_window_size(width, height)

        return driver

    def get_capabilities(self, config_section):
        """ Return dictionary of capabilities for specific config combination/

        :param str config_section: section in platform/environment.properties config
        :return: dict with capabilities
        """

        return {}

    def start_driver(self, browser_type, capabilities):
        """ Prepare selenium webdriver.

        :param str browser_type: type of browser for which prepare driver
        :param dict capabilities: capabilities used for webdriver initialization
        """

        raise NotImplementedError()

    def get_browser_profile(self, browser_type, capabilities):
        """ Return updated browser profile ready to be passed to driver.

        :param str browser_type: browser type (chrome, firefox, ..)
        :param dict capabilities: capabilities dict - can be updated
        :return: browser profile or None
        """

        # lowercase browser_type
        browser_type = browser_type.lower()
        crx_path = self.shishito_support.get_opt('with_extension')

        if browser_type == 'chrome':
            profile = webdriver.ChromeOptions()
            profile.add_argument('--ignore-certificate-errors')
            if crx_path:
                self.add_extension_to_browser(profile, crx_path)

        elif browser_type == 'firefox':
            profile = webdriver.FirefoxProfile()
            if crx_path:
                self.add_extension_to_browser(profile, crx_path)
        capabilities.update(profile.to_capabilities())

        return profile

    def get_pytest_arguments(self, config_section):
        """ Get environment specific arguments for pytest.

        :param config_section: section in platform/environment.properties config
        :return: dict with arguments for pytest or None
        """
        pass

    def get_test_name(self):
        """ Return test name from the call stack, assuming there can be only
        one "test\_" file in the stack. If there are more it means two PyTest
        tests ran when calling get_test_name, which is invalid use case.

        :return: test name or project_name setting
        """

        frames = inspect.getouterframes(inspect.currentframe())
        for frame in frames:
            if re.match('test_.*', os.path.basename(frame[1])):
                return os.path.basename(frame[1])[:-3]

        return self.shishito_support.get_opt('project_name')
