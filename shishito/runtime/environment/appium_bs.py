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
        browserstack = self.shishito_support.get_opt('browserstack')

        if browserstack:
            try:
                bs_user, bs_password = self.shishito_support.get_opt('browserstack').split(':', 1)
            except (AttributeError, ValueError):
                raise ValueError('Browserstack credentials were not specified! Unable to start browser.')

            if bs_user:
                #remote_url = 'http://%s@ondemand.saucelabs.com:80/wd/hub' % saucelabs
                remote_url = 'http://{0}:{1}@hub-cloud.browserstack.com/wd/hub'.format(bs_user, bs_password)
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

        capabilities= {
            'os': get_opt(config_section, 'os'),
            'os_version': get_opt(config_section, 'os_version'),
            'device': get_opt(config_section, 'device'),
            'app': get_opt('app') or get_opt(config_section, 'app'),
            'name': self.get_test_name() + time.strftime('_%Y-%m-%d'),
            'browserstack.debug': get_opt('browserstack_debug').lower() or False,
            'browserstack.appium_version':  get_opt(config_section, 'browserstack.appium_version') or '1.7.0',
            'deviceOrientation': get_opt(config_section, 'deviceOrientation') or 'portrait'
        }
        if(get_opt(config_section, 'os')=='android'):
            capabilities['autoGrantPermissions']= get_opt(config_section, 'autoGrantPermissions') or False
        if(get_opt(config_section, 'os')=='ios'):
            capabilities['autoAcceptAlerts'] = get_opt(config_section, 'autoAcceptAlerts').lower() or False
        return capabilities


    def get_pytest_arguments(self, config_section):
        """ Get environment specific arguments for pytest.

        :param config_section: section in platform/environment.properties config
        :return: dict with arguments for pytest or None
        """

        pytest_args = {
            '--os_version': '--os_version=%s' % self.shishito_support.get_opt(config_section, 'os_version'),
            '--device': '--device=%s' % self.shishito_support.get_opt(config_section, 'device'),
            '--app': '--app=%s' % (self.shishito_support.get_opt('app') or self.shishito_support.get_opt(config_section, 'app'))
        }
        browserstack = self.shishito_support.get_opt('browserstack')
        if browserstack:
            pytest_args['--browserstack'] = '--browserstack=%s' % browserstack

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
