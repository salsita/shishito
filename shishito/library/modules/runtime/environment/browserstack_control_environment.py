import inspect
import time
import re
import sys
import ntpath

from selenium import webdriver

from shishito.library.modules.runtime.environment.shishito_environment import ShishitoEnvironment
from shishito.library.modules.services.browserstack import BrowserStackAPI


class ControlEnvironment(ShishitoEnvironment):
    def __init__(self):
        ShishitoEnvironment.__init__(self)
        self.bs_api = BrowserStackAPI()
        self.platform_name = self.shishito_support.gid('test_platform')
        self.environment_name = self.shishito_support.gid('test_environment')
        self.config = self.shishito_support.get_environment_config(
            platform_name=self.platform_name,
            environment_name=self.environment_name)

    def call_browser(self, combination, capabilities=None):
        bs_auth = tuple(self.shishito_support.gid('browserstack').split(':'))
        if bs_auth:
            # wait until free browserstack session is available
            self.bs_api.wait_for_free_sessions(bs_auth,
                                               int(self.shishito_support.gid('session_waiting_time')),
                                               int(self.shishito_support.gid('session_waiting_delay')))

            # get browser capabilities and profile
            capabilities = self.get_capabilities(combination)
            hub_url = 'http://{0}:{1}@hub.browserstack.com:80/wd/hub'.format(*bs_auth)

            # call remote driver
            driver = self.start_driver(hub_url, capabilities)

            session = self.bs_api.get_session(bs_auth, capabilities['build'], 'running')
            self.session_link = self.bs_api.get_session_link(session)
            self.session_id = self.bs_api.get_session_hashed_id(session)
            return driver
        else:
            sys.exit('Browserstack credentials were not specified! Unable to start browser.')

    def start_driver(self, remote_driver_url, capabilities, browser_type=None):
        """ Starts driver """
        browser_profile = self.get_browser_profile(browser_type, capabilities)

        driver = webdriver.Remote(
            command_executor=remote_driver_url,
            desired_capabilities=capabilities,
            browser_profile=browser_profile)
        return driver

    def get_capabilities(self, combination):
        """Returns dictionary of capabilities for specific Browserstack browser/os combination """
        build_name = self.shishito_support.gid('build_name')
        # test_mobile = self.shishito_support.gid('test_mobile')
        capabilities = {
            'acceptSslCerts': self.shishito_support.gid('accept_ssl_cert').lower() == 'false',
            'browserstack.debug': self.shishito_support.gid('browserstack_debug').lower(),
            'project': self.shishito_support.gid('project_name'),
            'build': build_name,
            'name': self.get_test_name() + time.strftime('_%Y-%m-%d')
        }
        # TODO take this information (test mobile) from "platform" module
        # if test_mobile == 'yes':
        # capabilities.update({
        #         'device': self.config['device'],
        #         'platform': self.config['platform'],
        #         'deviceOrientation': self.config['deviceOrientation'],
        #         'browserName': self.config['browserName'],
        #     })
        # else:
        capabilities.update({
            'os': self.config.get(combination, 'os'),
            'os_version': self.config.get(combination, 'os_version'),
            'browser': self.config.get(combination, 'browser'),
            'browser_version': self.config.get(combination, 'browser_version'),
            'resolution': self.config.get(combination, 'resolution'),
        })
        return capabilities

    def get_browser_profile(self, browser_type, capabilities):
        """ Returns updated browser profile ready to be passed to driver """
        profile = None

        # add extensions to remote driver
        if self.shishito_support.gid('with_extension'):
            # browser_profile = self.add_extension_to_browser(browser_type, browser_profile)
            pass

        if browser_type == 'chrome':
            chrome_options = webdriver.ChromeOptions()
            chrome_options.add_experimental_option("excludeSwitches", ["ignore-certificate-errors"])
            capabilities.update(chrome_options.to_capabilities())
        elif browser_type == 'firefox':
            profile = webdriver.FirefoxProfile()
        return profile

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