from __future__ import absolute_import

from selenium import webdriver

from shishito.runtime.environment.shishito import ShishitoEnvironment


class ControlEnvironment(ShishitoEnvironment):
    """ Local control environment. """

    def get_capabilities(self, config_section):
        """ Return dictionary of capabilities for specific config combination.
        :param str config_section: section in platform/environment.properties config
        :return: dict with capabilities
        """

        get_opt = self.shishito_support.get_opt
        default_capabilities = super().get_capabilities(config_section)
        capabilities = {
            'marionette': str(get_opt('firefox_marionette')).lower() == 'true',
        }
        return {**default_capabilities, **capabilities}

    def start_driver(self, browser_type, capabilities, config_section=None):
        """ Prepare selenium webdriver.

        :param browser_type: type of browser for which prepare driver
        :param capabilities: capabilities used for webdriver initialization
        """

        # get browser profile
        browser_profile = self.get_browser_profile(browser_type, capabilities, config_section)

        # starts local browser
        if browser_type == "firefox":
            from selenium.webdriver.firefox.options import Options
            firefox_options = Options()
            for arg in self.get_browser_arguments(config_section):
                firefox_options.add_argument(arg)
            driver = webdriver.Firefox(browser_profile, desired_capabilities=capabilities,
                                       firefox_options=firefox_options)
        elif browser_type == "chrome":
            driver = webdriver.Chrome(desired_capabilities=capabilities, chrome_options=browser_profile)
        elif browser_type == "ie":
            driver = webdriver.Ie(capabilities=capabilities)
        elif browser_type == "phantomjs":
            driver = webdriver.PhantomJS(desired_capabilities=capabilities)
        elif browser_type == "opera":
            driver = webdriver.Opera(desired_capabilities=capabilities)
            # SafariDriver bindings for Python not yet implemented
            # elif browser == "Safari":
            # self.driver = webdriver.SafariDriver()
        else:
            raise ValueError('Unknown type of browser.')

        return driver

    def call_browser(self, config_section):
        """ Start webdriver for given config section. Prepare capabilities for the browser, set browser resolution.

        :param str config_section: section in platform/environment.properties config
        :return: created webdriver
        """

        # get browser capabilities
        capabilities = self.get_capabilities(config_section)

        # get browser type
        browser_type = self.shishito_support.get_opt(config_section, 'browser').lower()

        # get driver
        driver = self.start_driver(browser_type, capabilities, config_section=config_section)
        if browser_type.lower() == 'chrome':
            self.set_download_path(driver)

        # set browser size is defined
        browser_size = self.shishito_support.get_opt(config_section, 'resolution')
        if browser_size:
            # default size --> leave it on webdriver
            width, height = browser_size.split('x')
            driver.set_window_size(width, height)

        return driver
