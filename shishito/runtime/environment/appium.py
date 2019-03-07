from __future__ import absolute_import

from appium import webdriver
import time

from shishito.runtime.environment.shishito import ShishitoEnvironment


class ControlEnvironment(ShishitoEnvironment):
    """ Appium control environment. """

    def call_browser(self, config_section):
        """ Start webdriver for given config section. Prepare capabilities for the webdriver. If saucelabs setting has value,
        webdriver will be connected to saucelabs. Otherwise appium_url setting will be used.

        :param str config_section: section in platform/environment.properties config
        :return: created webdriver
        """

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
        """ Return dictionary of capabilities for specific config combination.

        :param str config_section: section in platform/environment.properties config
        :return: dict with capabilities
        """

        get_opt = self.shishito_support.get_opt

        return {
            'platformName': get_opt(config_section, 'platformName'),
            'platformVersion': get_opt(config_section, 'platformVersion'),
            'deviceName': get_opt(config_section, 'deviceName'),
            'app': get_opt('app') or get_opt(config_section, 'app'),
            'appiumVersion': get_opt(config_section, 'appiumVersion') or '1.6.5',
            'autoAcceptAlerts': None or get_opt(config_section, 'autoAcceptAlerts') == 'true',  # default False
            'waitForQuiescence': None or get_opt(config_section, 'waitForQuiescence') == 'true',  # default False
        }

    def get_pytest_arguments(self, config_section):
        """ Get environment specific arguments for pytest.

        :param config_section: section in platform/environment.properties config
        :return: dict with arguments for pytest or None
        """

        pytest_args = {
            '--platformName': '--platformName=%s' % self.shishito_support.get_opt(config_section, 'platformName'),
            '--platformVersion': '--platformVersion=%s' % self.shishito_support.get_opt(config_section, 'platformVersion'),
            '--deviceName': '--deviceName=%s' % self.shishito_support.get_opt(config_section, 'deviceName'),
            '--autoAcceptAlerts': '--autoAcceptAlerts=%s' % self.shishito_support.get_opt(config_section, 'autoAcceptAlerts'),
            '--app': '--app=%s' % (self.shishito_support.get_opt('app') or self.shishito_support.get_opt(config_section, 'app'))
        }

        saucelabs = self.shishito_support.get_opt('saucelabs')
        if saucelabs:
            pytest_args['--saucelabs'] = '--saucelabs=%s' % saucelabs
        return pytest_args

    def start_driver(self, capabilities, remote_driver_url):
        """ Prepare selenium webdriver.

        :param capabilities: capabilities used for webdriver initialization
        :param remote_driver_url: url to which the driver will be connected
        """

        driver = webdriver.Remote(
            command_executor=remote_driver_url,
            desired_capabilities=capabilities,
        )

        return driver
