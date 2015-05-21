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

        return {
            'acceptSslCerts': get_opt('accept_ssl_cert').lower() == 'false',
        }

    def start_driver(self, browser_type, capabilities):
        """ Prepare selenium webdriver.

        :param browser_type: type of browser for which prepare driver
        :param capabilities: capabilities used for webdrivre initialization
        """

        # get browser profile
        browser_profile = self.get_browser_profile(browser_type, capabilities)

        # starts local browser
        if browser_type == "firefox":
            driver = webdriver.Firefox(browser_profile, capabilities=capabilities)
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
