from __future__ import absolute_import

from appium import webdriver
import time

from shishito.runtime.environment.shishito import ShishitoEnvironment


class ControlEnvironment(ShishitoEnvironment):
    """ Appium control environment. """

    def call_browser(self, config_section):
        """ Starts browser """

        # get browser capabilities
        capabilities = self.get_capabilities(config_section)

        saucelabs = self.shishito_support.get_opt('saucelabs')
        if saucelabs:
            remote_url = 'http://%s@ondemand.saucelabs.com:80/wd/hub' % saucelabs
        else:
            remote_url = self.shishito_support.get_opt('appium_url')

        # get driver
        return self.start_driver(capabilities, remote_url)

    def get_capabilities(self, config_section):
        """ Returns dictionary of capabilities for specific Browserstack browser/os combination """

        get_opt = self.shishito_support.get_opt

        return {
            'platformName': get_opt(config_section, 'platformName'),
            'platformVersion': get_opt(config_section, 'platformVersion'),
            'deviceName': get_opt(config_section, 'deviceName'),
            'app': get_opt(config_section, 'app'),
            'appiumVersion': get_opt(config_section, 'appiumVersion'),
            'name': self.get_test_name() + time.strftime('_%Y-%m-%d'),
        }

    def get_pytest_arguments(self, config_section):
        """ """

        pytest_args = {
            '--platformName': '--platformName=%s' % self.shishito_support.get_opt(config_section, 'platformName'),
            '--platformVersion': '--platformVersion=%s' % self.shishito_support.get_opt(config_section, 'platformVersion'),
            '--deviceName': '--deviceName=%s' % self.shishito_support.get_opt(config_section, 'deviceName'),
            '--app': '--app=%s' % self.shishito_support.get_opt(config_section, 'app'),
        }

        saucelabs = self.shishito_support.get_opt('saucelabs')
        if saucelabs:
            pytest_args['--saucelabs'] = '--saucelabs=%s' % saucelabs

        return pytest_args

    def start_driver(self, capabilities, remote_driver_url):
        """ """

        driver = webdriver.Remote(
            command_executor=remote_driver_url,
            desired_capabilities=capabilities,
        )

        return driver
