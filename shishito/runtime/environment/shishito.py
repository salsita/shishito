import inspect
import os
import re
from selenium import webdriver


class ShishitoEnvironment(object):

    def __init__(self, shishito_support):
        self.shishito_support = shishito_support

    def add_extension_to_browser(self, browser_type, browser_profile):
        """ returns browser profile updated with one or more extensions """

        if browser_type == 'chrome':
            all_extensions = self.get_extension_file_names('crx')
            for chr_extension in all_extensions:
                browser_profile.add_extension(os.path.join(self.shishito_support.project_root, 'extension', chr_extension + '.crx'))

        elif browser_type == 'firefox':
            all_extensions = self.get_extension_file_names('xpi')
            for ff_extension in all_extensions:
                browser_profile.add_extension(os.path.join(self.shishito_support.project_root, 'extension', ff_extension + '.xpi'))

        return browser_profile

    def call_browser(self, config_section):
        """ Starts browser """

        # get browser capabilities
        capabilities = self.get_capabilities(config_section)

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
        """ Returns dictionary of capabilities for specific Browserstack browser/os combination """

        return {}

    def start_driver(self, browser_type, capabilities):
        """ Starts driver """

        raise NotImplementedError()

    def get_browser_profile(self, browser_type, capabilities):
        """ Returns updated browser profile ready to be passed to driver """

        # lowercase browser_type
        browser_type = browser_type.lower()

        profile = None

        if browser_type == 'chrome':
            chrome_options = webdriver.ChromeOptions()
            chrome_options.add_experimental_option("excludeSwitches", ["ignore-certificate-errors"])
            capabilities.update(chrome_options.to_capabilities())
        elif browser_type == 'firefox':
            profile = webdriver.FirefoxProfile()

        if profile is None:
            return None

        # add extensions to remote driver
        if self.shishito_support.get_opt('with_extension'):
            # TODO: add support for extensions again
            # profile = self.add_extension_to_browser(browser_type, profile)
            pass

        # add Chrome options to desired capabilities
        if browser_type == 'chrome':
            chrome_capabilities = profile.to_capabilities()
            capabilities.update(chrome_capabilities)
            profile = None

        return profile

    def get_pytest_arguments(self, config_section):
        """ Get environment specific arguments for pytest. """
        pass

    def get_test_name(self):
        """ Returns test name from the call stack, assuming there can be only
         one 'test_' file in the stack. If there are more it means two PyTest
        tests ran when calling get_test_name, which is invalid use case. """
        frames = inspect.getouterframes(inspect.currentframe())
        for frame in frames:
            if re.match('test_.*', os.path.basename(frame[1])):
                return os.path.basename(frame[1])[:-3]

        return self.shishito_support.get_opt('project_name')
