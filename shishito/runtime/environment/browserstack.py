from __future__ import absolute_import

from selenium import webdriver
import sys
import time

from shishito.runtime.environment.shishito import ShishitoEnvironment
from shishito.services.browserstack import BrowserStackAPI


class ControlEnvironment(ShishitoEnvironment):
    """ Browserstack control environment. """

    def __init__(self, shishito_support):
        super(ControlEnvironment, self).__init__(shishito_support)

        self.bs_api = BrowserStackAPI()

    def call_browser(self, config_section):
        """ Start webdriver for given config section. Wait for free browserstack session.
        Prepare capabilities for the browser. Created webdriver will be connected to browserstack.

        :param str config_section: section in platform/environment.properties config
        :return: created webdriver
        """

        # get browser stack credentials
        try:
            bs_user, bs_password = self.shishito_support.get_opt('browserstack').split(':', 1)
        except (AttributeError, ValueError):
            raise ValueError('Browserstack credentials were not specified! Unable to start browser.')

        # wait until free browserstack session is available
        if not self.bs_api.wait_for_free_sessions(
            (bs_user, bs_password),
            int(self.shishito_support.get_opt('session_waiting_time')),
            int(self.shishito_support.get_opt('session_waiting_delay'))
        ):
            sys.exit('No free browserstack session - exit.')

        # get browser capabilities
        capabilities = self.get_capabilities(config_section)

        # prepare remote driver url
        hub_url = 'http://{0}:{1}@hub.browserstack.com:80/wd/hub'.format(bs_user, bs_password)

        # get browser type
        browser_type = self.shishito_support.get_opt(config_section, 'browser')
        browser_type = browser_type.lower()

        # call remote driver
        driver = self.start_driver(browser_type, capabilities, remote_driver_url=hub_url)

        session = self.bs_api.get_session((bs_user, bs_password), capabilities['build'], 'running')
        self.session_link = self.bs_api.get_session_link(session)
        self.session_id = self.bs_api.get_session_hashed_id(session)

        return driver

    def get_pytest_arguments(self, config_section):
        """ Get environment specific arguments for pytest.

        :param config_section: section in platform/environment.properties config
        :return: dict with arguments for pytest or None
        """
        test_platform = self.shishito_support.test_platform
        arguments = {}
        if(test_platform == 'web'):
            browser = self.shishito_support.get_opt(config_section, 'browser')
            browser_version = self.shishito_support.get_opt(config_section, 'browser_version')
            os_type = self.shishito_support.get_opt(config_section, 'os')
            os_version = self.shishito_support.get_opt(config_section, 'os_version')
            resolution = self.shishito_support.get_opt(config_section, 'resolution')
            test_result_prefix = '[%s, %s, %s, %s, %s]' % (
            browser, browser_version, os_type, os_version, resolution
            )

            # Add browserstack credentials
            bs_auth = self.shishito_support.get_opt('browserstack')

            # prepare pytest arguments into execution list
            return {
                '--junit-prefix=': '--junit-prefix=' + test_result_prefix,
                '--html-prefix=': '--html-prefix=' + test_result_prefix,
                '--browser=': '--browser=' + browser,
                '--browser_version=': '--browser_version=' + browser_version,
                '--os=': '--os=' + os_type,
                '--os_version=': '--os_version=' + os_version,
                '--resolution=': '--resolution=' + resolution,
                '--browserstack=': '--browserstack=' + bs_auth
                }
        if(test_platform == 'mobile'):
            browser = self.shishito_support.get_opt(config_section, 'browser')
            platform = self.shishito_support.get_opt(config_section, 'platform')
            device = self.shishito_support.get_opt(config_section, 'device')
            deviceOrientation = self.shishito_support.get_opt(config_section, 'deviceOrientation') or 'portrait'

            test_result_prefix = '[%s, %s, %s]' % (
                browser, platform, device
            )

            # Add browserstack credentials
            bs_auth = self.shishito_support.get_opt('browserstack')

            # prepare pytest arguments into execution list
            return {
                '--junit-prefix=': '--junit-prefix=' + test_result_prefix,
                '--html-prefix=': '--html-prefix=' + test_result_prefix,
                '--browser=': '--browser=' + browser,
                '--platform=': '--platform=' + platform,
                '--device=': '--device=' + device,
                '--deviceOrientation=': '--deviceOrientation=' + deviceOrientation,
                '--browserstack=': '--browserstack=' + bs_auth
            }

    def get_capabilities(self, config_section):
        """ Return dictionary of capabilities for specific config combination.

        :param str config_section: section in platform/environment.properties config
        :return: dict with capabilities
        """

        test_platform = self.shishito_support.test_platform
        get_opt = self.shishito_support.get_opt

        default_capabilities = super().get_capabilities(config_section)
        special_capabilities = {}
        capabilities = {
            'browserstack.debug': get_opt('browserstack_debug').lower(),
            'project': get_opt('project_name'),
            'build': get_opt('build_name'),
            'name': self.get_test_name() + time.strftime('_%Y-%m-%d'),
            'browserstack.local': get_opt('browserstack_local') or False
             }
        if(test_platform == 'web'):
            special_capabilities = {
                'os': get_opt(config_section, 'os'),
                'os_version': get_opt(config_section, 'os_version'),
                'browser': get_opt(config_section, 'browser'),
                'browser_version': get_opt(config_section, 'browser_version'),
                'resolution': get_opt(config_section, 'resolution')
            }
        if(test_platform == 'mobile'):
            special_capabilities = {
                'browser': get_opt(config_section, 'browser'),
                'platform': get_opt(config_section, 'platform'),
                'device': get_opt(config_section, 'device'),
                'deviceOrientation': get_opt(config_section, 'deviceOrientation') or 'portrait'
            }
        self.add_cmdline_arguments_to_browser(capabilities, config_section)
        return {**default_capabilities, **capabilities, **special_capabilities}
    # TODO will need to implement some edge cases from there (mobile emulation etc..)
    # def get_browser_profile(self, browser_type):
    # """ returns ChromeOptions or FirefoxProfile with default settings, based on browser """
    # if browser_type.lower() == 'chrome':
    #         profile = webdriver.ChromeOptions()
    #         profile.add_experimental_option("excludeSwitches", ["ignore-certificate-errors"])
    #         # set mobile device emulation
    #         mobile_browser_emulation = self.gid('mobile_browser_emulation')
    #         if mobile_browser_emulation:
    #             profile.add_experimental_option("mobileEmulation", {"deviceName": mobile_browser_emulation})
    #         return profile
    #     elif browser_type.lower() == 'firefox':
    #         return webdriver.FirefoxProfile()
    #
    # def update_browser_profile(self, capabilities, browser_type=None):
    #     """ Returns updated browser profile ready to be passed to driver """
    #     browser_profile = None
    #     test_mobile = self.gid('test_mobile')
    #     appium_platform = self.gid('appium_platform')
    #     if test_mobile != 'yes' and appium_platform not in ('android', 'ios'):
    #         if browser_type is None:
    #             browser_type = capabilities['browser'].lower()
    #         browser_profile = self.get_browser_profile(browser_type)
    #
    #         # add extensions to remote driver
    #         if self.gid('with_extension'):
    #             browser_profile = self.add_extension_to_browser(browser_type, browser_profile)
    #
    #         # add Chrome options to desired capabilities
    #         if browser_type == 'chrome':
    #             chrome_capabilities = browser_profile.to_capabilities()
    #             capabilities.update(chrome_capabilities)
    #             browser_profile = None
    #     return browser_profile

    def start_driver(self, browser_type, capabilities, remote_driver_url):
        """ Prepare selenium webdriver.

        :param browser_type: type of browser for which prepare driver
        :param capabilities: capabilities used for webdriver initialization
        :param remote_driver_url: browserstack url, to which the driver will be connected
        """

        browser_profile = self.get_browser_profile(browser_type, capabilities)

        driver = webdriver.Remote(
            command_executor=remote_driver_url,
            desired_capabilities=capabilities,
            browser_profile=browser_profile)

        return driver
