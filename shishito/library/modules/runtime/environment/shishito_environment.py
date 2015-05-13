import os
from selenium import webdriver
import sys


class ShishitoEnvironment(object):

    def __init__(self, shishito_support):
        self.shishito_support = shishito_support
        self.capabilities = None

        self.config = self.shishito_support.get_environment_config()

        self.project_root = os.getcwd()

    def add_extension_to_browser(self, browser_type, browser_profile):
        """ returns browser profile updated with one or more extensions """

        if browser_type == 'chrome':
            all_extensions = self.get_extension_file_names('crx')
            for chr_extension in all_extensions:
                browser_profile.add_extension(os.path.join(self.project_root, 'extension', chr_extension + '.crx'))
        elif browser_type == 'firefox':
            all_extensions = self.get_extension_file_names('xpi')
            for ff_extension in all_extensions:
                browser_profile.add_extension(os.path.join(self.project_root, 'extension', ff_extension + '.xpi'))

        return browser_profile

    def call_browser(self, combination, capabilities=None):
        """ Starts browser """

        # get browser capabilities and profile
        if capabilities:
            capabilities.update(self.get_capabilities(combination))
        else:
            capabilities = self.get_capabilities(combination)

        # get browser type
        browser_type = self.config.get(combination, 'browser')
        browser_type = browser_type.lower()

        # get driver
        driver = self.start_driver(browser_type, capabilities)

        # set browser size is defined
        browser_size = self.config.get(combination, 'resolution')
        if browser_size:
            # default size --> leave it on webdriver
            width, height = browser_size.split('x')
            driver.set_window_size(width, height)

        return driver

    def get_capabilities(self, combination):
        """ Returns dictionary of browser capabilities """
        pass

    def start_driver(self, browser_type, capabilities, remote_driver_url):
        """ Starts driver """

        browser_profile = self.get_browser_profile(browser_type, capabilities)

        if not remote_driver_url:
            sys.exit('Base start driver: missing remote_driver_url')

        driver = webdriver.Remote(
            command_executor=remote_driver_url,
            desired_capabilities=capabilities,
            browser_profile=browser_profile)

        return driver

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
        if self.shishito_support.gid('with_extension'):
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
