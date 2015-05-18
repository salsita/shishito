from appium import webdriver
#from selenium import webdriver
import time

from shishito.library.modules.runtime.environment.shishito_environment import ShishitoEnvironment


class ControlEnvironment(ShishitoEnvironment):
    """ Appium control environment. """

    CAPABILITIES = (
        ('platformName', 'platformName', True, None),
        ('platformVersion', 'platformVersion', True, None),
        ('deviceName', 'deviceName', True, None),
        ('app', 'app', True, None),
        ('appiumVersion', 'appiumVersion', True, None),
    )

    def call_browser(self, combination, capabilities=None):
        """ Starts browser """

        # get browser capabilities and profile
        if capabilities:
            capabilities.update(self.get_capabilities(combination))
        else:
            capabilities = self.get_capabilities(combination)

        use_saucelabs = self.shishito_support.gid('use_saucelabs')
        if use_saucelabs is not None and use_saucelabs.lower() == 'true':
            saucelabs = self.shishito_support.gid('saucelabs')
            remote_url = 'http://%s@ondemand.saucelabs.com:80/wd/hub' % saucelabs
        else:
            remote_url = self.shishito_support.gid('appium_url')

        # get driver
        return self.start_driver(capabilities, remote_url)

    def get_capabilities(self, combination):
        """ Returns dictionary of capabilities for specific Browserstack browser/os combination """

        capabilities = super(ControlEnvironment, self).get_capabilities(combination)
        capabilities['name'] = self.get_test_name() + time.strftime('_%Y-%m-%d')
        return capabilities

    def get_pytest_arguments(self, config_section):
        """ """

        pytest_args = {
            '--platformName': '--platformName=%s' % self.shishito_support.gid('platformName', config_section),
            '--platformVersion': '--platformVersion=%s' % self.shishito_support.gid('platformVersion', config_section),
            '--deviceName': '--deviceName=%s' % self.shishito_support.gid('deviceName', config_section),
            '--app': '--app=%s' % self.shishito_support.gid('app', config_section),
        }

        use_saucelabs = self.shishito_support.gid('use_saucelabs')
        if use_saucelabs is not None and use_saucelabs.lower() == 'true':
            saucelabs = self.shishito_support.gid('saucelabs')
            pytest_args['--saucelabs'] = '--saucelabs=%s' % saucelabs

        return pytest_args

    def start_driver(self, capabilities, remote_driver_url):
        """ """

        driver = webdriver.Remote(
            command_executor=remote_driver_url,
            desired_capabilities=capabilities,
        )

        return driver
