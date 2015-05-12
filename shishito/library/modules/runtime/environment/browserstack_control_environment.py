import inspect
import ntpath
import os
import re
import sys
import time

from shishito.library.modules.runtime.environment.shishito_environment import ShishitoEnvironment
from shishito.library.modules.services.browserstack import BrowserStackAPI


class ControlEnvironment(ShishitoEnvironment):
    """ Browserstack control environment. """

    def __init__(self, shishito_support):
        super(ControlEnvironment, self).__init__(shishito_support)

        self.bs_api = BrowserStackAPI()

        self.project_root = os.getcwd() # TODO:
        self.timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
        self.result_folder = os.path.join(self.project_root, 'results', self.timestamp)

    def call_browser(self, combination, capabilities=None):
        """ Starts browser """

        # get browser stack credentials
        bs_auth = tuple(self.shishito_support.gid('browserstack').split(':'))
        if not bs_auth:
            sys.exit('Browserstack credentials were not specified! Unable to start browser.')

        # wait until free browserstack session is available
        if not self.bs_api.wait_for_free_sessions(
            bs_auth,
            int(self.shishito_support.gid('session_waiting_time')),
            int(self.shishito_support.gid('session_waiting_delay'))
        ):
            sys.exit('No free browserstack session - exit.')

        # get browser capabilities and profile
        capabilities = self.get_capabilities(combination)

        # prepare remote driver url
        hub_url = 'http://{0}:{1}@hub.browserstack.com:80/wd/hub'.format(*bs_auth)

        # get browser type
        browser_type = self.config.get(combination, 'browser')
        browser_type = browser_type.lower()

        # call remote driver
        driver = self.start_driver(browser_type, capabilities, remote_driver_url=hub_url)

        session = self.bs_api.get_session(bs_auth, capabilities['build'], 'running')
        self.session_link = self.bs_api.get_session_link(session)
        self.session_id = self.bs_api.get_session_hashed_id(session)

        return driver

    def get_pytest_arguments(self, config_section):
        """ Get environment specific arguments for pytest. """

        browser = self.config.get(config_section, 'browser')
        browser_version = self.config.get(config_section, 'browser_version')
        os_type = self.config.get(config_section, 'os')
        os_version = self.config.get(config_section, 'os_version')
        resolution = self.config.get(config_section, 'resolution')
        junit_xml_path = os.path.join(self.result_folder, config_section + '.xml')
        html_path = os.path.join(self.result_folder, config_section + '.html')

        test_result_prefix = '[%s, %s, %s, %s, %s]' % (
            browser, browser_version, os_type, os_version, resolution
        )

        # Add browserstack credentials
        bs_auth = self.shishito_support.gid('browserstack')

        # prepare pytest arguments into execution list
        return {
            '--junitxml=': '--junitxml=' + junit_xml_path,
            '--junit-prefix=': '--junit-prefix=' + test_result_prefix,
            '--html=': '--html=' + html_path,
            '--html-prefix=': '--html-prefix=' + test_result_prefix,
            '--xbrowser=': '--xbrowser=' + browser,
            '--xbrowserversion=': '--xbrowserversion=' + browser_version,
            '--xos=': '--xos=' + os_type,
            '--xosversion=': '--xosversion=' + os_version,
            '--xresolution=': '--xresolution=' + resolution,
            '--browserstack=': '--browserstack=' + bs_auth,
        }

    def get_capabilities(self, combination):
        """ Returns dictionary of capabilities for specific Browserstack browser/os combination """

        build_name = self.shishito_support.gid('build_name')

        capabilities = {
            'acceptSslCerts': self.shishito_support.gid('accept_ssl_cert').lower() == 'false',
            'browserstack.debug': self.shishito_support.gid('browserstack_debug').lower(),
            'project': self.shishito_support.gid('project_name'),
            'build': build_name,
            'name': self.get_test_name() + time.strftime('_%Y-%m-%d'),
            'os': self.config.get(combination, 'os'),
            'os_version': self.config.get(combination, 'os_version'),
            'browser': self.config.get(combination, 'browser'),
            'browser_version': self.config.get(combination, 'browser_version'),
            'resolution': self.config.get(combination, 'resolution'),
        }

        return capabilities

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

    def get_test_name(self):
        """ Returns test name from the call stack, assuming there can be only
         one 'test_' file in the stack. If there are more it means two PyTest
        tests ran when calling get_test_name, which is invalid use case. """
        frames = inspect.getouterframes(inspect.currentframe())
        for frame in frames:
            if re.match('test_.*', ntpath.basename(frame[1])):
                return ntpath.basename(frame[1])[:-3]

        return self.shishito_support.gid('project_name')
