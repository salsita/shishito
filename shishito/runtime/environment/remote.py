from __future__ import absolute_import

from selenium import webdriver

from shishito.runtime.environment.shishito import ShishitoEnvironment


class ControlEnvironment(ShishitoEnvironment):
    """ Remote control environment. """

    def call_browser(self, config_section):
        """ Starts browser """

        # get browser capabilities
        capabilities = self.get_capabilities(config_section)

        # get remote url
        remote_url = self.shishito_support.get_opt('remote_driver_url')

        # get driver
        return self.start_driver(capabilities, remote_url)

    def get_capabilities(self, config_section):
        """ Returns dictionary of capabilities for specific Browserstack browser/os combination """

        get_opt = self.shishito_support.get_opt

        return {
            'acceptSslCerts': get_opt('accept_ssl_cert').lower() == 'false',
            'browserName': get_opt(config_section, 'browser'),
            'browser_version': get_opt(config_section, 'browser_version'),
            'resolution': get_opt(config_section, 'resolution'),
            'javascriptEnabled': True
        }

    def start_driver(self, capabilities, remote_driver_url):
        """ Call remote browser (driver) """

        driver = webdriver.Remote(
            command_executor=remote_driver_url,
            desired_capabilities=capabilities)

        return driver
