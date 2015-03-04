# /usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: Vojtech Burian
@summary: Common configuration functions supporting test execution.
 Various startup and termination procedures, helper functions etc.
 Not to be used for directly testing the system under test (must not contain Asserts etc.)
"""
import ConfigParser
import os
import sys
import inspect
import time
import re
import ntpath
import glob
import shutil
import subprocess
from datetime import datetime

from selenium import webdriver
import pytest
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

from salsa_webqa.library.support.browserstack import BrowserStackAPI
from salsa_webqa.library.support.jira_zephyr_api import ZAPI


class ControlTest(object):
    def __init__(self):
        self.bs_api = BrowserStackAPI()
        self.zapi = ZAPI()
        self.project_root = self.get_project_root()
        self.configs = self.load_configs()
        self.session_link = None
        self.session_id = None
        self.driver = None
        self.bs_config_file = os.path.join(self.project_root, 'config', 'web.properties')
        self.config = ConfigParser.RawConfigParser()

    def get_project_root(self):
        project_root = os.environ.get('SALSA_WEBQA_PROJECT')
        # if OS environment variable is not defined it means that test is being run directly (without runner).
        # In this casse call-stack is used to determine the correct project folder.
        if project_root is None:
            project_root = os.path.abspath(
                os.path.join(os.path.dirname(inspect.getsourcefile(sys._getframe(2))), os.pardir))
            os.environ['SALSA_WEBQA_PROJECT'] = project_root
        return project_root

    def load_configs(self):
        """ Loads variables from .properties configuration files,  check if project didn't contain such folder
        (for non selenium projects) """
        config_path = os.path.join(self.project_root, 'config')
        config = ConfigParser.ConfigParser()
        if os.path.exists(config_path):
            # load server config variables
            server_config = os.path.join(config_path, 'server_config.properties')
            config.read(server_config)
            server_config_vars = dict(config.defaults())
            # load local config variables
            local_config = os.path.join(config_path, 'local_config.properties')
            config.read(local_config)
            local_config_vars = dict(config.defaults())
            # load non selenium config variables
            non_selenium_config = os.path.join(config_path, 'non_selenium_config.properties')
            config.read(non_selenium_config)
            non_selenium_config = dict(config.defaults())
            return_configs = [server_config_vars, local_config_vars, non_selenium_config]
            return return_configs

    def gid(self, key):
        """ Gets value from config variables based on provided key.
         If local execution parameter is "True", function will try to search for parameter in local configuration file.
         If such parameter is not found or there is an error while reading the file, server (default) configuration
         file will be used instead. """
        if not self.configs:
            return None

        # first try to lookup pytest config
        try:
            value = pytest.config.getoption(key)
            if value:
                return value
            else:
                use_logs = True
        except (ValueError, AttributeError):
            use_logs = True
        # lookup value from config files
        if use_logs:
            server_config = self.configs[0]
            local_config = self.configs[1]
            configs = []
            if local_config.get('local_execution').lower() == 'true':
                configs.append((local_config, 'local config'))
            configs.extend([(server_config, 'server config'), (os.environ, 'env variables')])
            for idx, cfg in enumerate(configs):
                if key in cfg[0] and cfg[0][key] != '':
                    # if idx:
                    # print "%s not found in %s, using value from %s" % (key, configs[0][1], cfg[1])
                    return cfg[0][key]
                    # print "%s not found in any config" % key

    def get_browserstack_capabilities(self, build_name=None):
        """Returns dictionary of capabilities for specific Browserstack browser/os combination """
        build_name = build_name or self.gid('build_name')
        cfg = pytest.config
        test_mobile = self.gid('test_mobile')
        capabilities = {
            'browserstack.debug': self.gid('browserstack_debug').lower(),
            'project': self.gid('project_name'),
            'build': build_name,
            'name': self.get_test_name() + time.strftime('_%Y-%m-%d')
        }
        if test_mobile == 'yes':
            capabilities.update({
                'device': cfg.getoption('xdevice'),
                'platform': cfg.getoption('xplatform'),
                'deviceOrientation': cfg.getoption('xdeviceOrientation'),
                'browserName': cfg.getoption('xbrowserName'),
            })
        else:
            capabilities.update({
                'os': cfg.getoption('xos'),
                'os_version': cfg.getoption('xosversion'),
                'browser': cfg.getoption('xbrowser'),
                'browser_version': cfg.getoption('xbrowserversion'),
                'resolution': cfg.getoption('xresolution'),
            })
        return capabilities

    def get_appium_capabilities(self, platform):
        """Returns dictionary of capabilities for specific Appium combination """
        cfg = pytest.config
        if platform == 'ios':
            capabilities = {
                'platformName': cfg.getoption('platformName'),
                'platformVersion': cfg.getoption('platformVersion'),
                'deviceName': cfg.getoption('deviceName'),
                'appiumVersion': cfg.getoption('appiumVersion'),
                'app': cfg.getoption('app')
            }
        elif platform == 'android':
            capabilities = {
                'platformName': cfg.getoption('platformName'),
                'platformVersion': cfg.getoption('platformVersion'),
                'deviceName': cfg.getoption('deviceName'),
                'appPackage': cfg.getoption('appPackage'),
                'appActivity': cfg.getoption('appActivity'),
                'appiumVersion': cfg.getoption('appiumVersion'),
                'app': cfg.getoption('app')
            }
            capabilities = {c: cfg.getoption(c) for c in []}
        else:
            sys.exit('Incorrect platform was specified. Acceptable values: "ios", "android".')
        return capabilities

    def get_capabilities(self, build_name=None, browserstack=False, appium_platform=False):
        """ Returns dictionary of browser capabilities """
        desired_cap = {
            'acceptSslCerts': self.gid('accept_ssl_cert').lower() == 'false'
        }
        if browserstack:
            desired_cap.update(self.get_browserstack_capabilities(build_name))
        if appium_platform:
            desired_cap.update(self.get_appium_capabilities(appium_platform))
        return desired_cap

    def get_test_name(self):
        """ Returns test name from the call stack, assuming there can be only
         one 'test_' file in the stack. If there are more it means two PyTest
        tests ran when calling get_test_name, which is invalid use case. """
        frames = inspect.getouterframes(inspect.currentframe())
        for frame in frames:
            if re.match('test_.*', ntpath.basename(frame[1])):
                return ntpath.basename(frame[1])[:-3]

        return self.gid('project_name')

    def get_default_browser_attributes(self, browser, height, url, width):
        """ Returns default browser values if not initially set """
        return (
            browser or self.gid('driver'),
            height or self.gid('window_height'),
            url or self.gid('base_url'),
            width or self.gid('window_width')
        )

    def get_browser_profile(self, browser_type):
        """ returns ChromeOptions or FirefoxProfile with default settings, based on browser """
        if browser_type.lower() == 'chrome':
            profile = webdriver.ChromeOptions()
            profile.add_experimental_option("excludeSwitches", ["ignore-certificate-errors"])
            # set mobile device emulation
            mobile_browser_emulation = self.gid('mobile_browser_emulation')
            if mobile_browser_emulation:
                profile.add_experimental_option("mobileEmulation", {"deviceName": mobile_browser_emulation})
            return profile
        elif browser_type.lower() == 'firefox':
            return webdriver.FirefoxProfile()

    def update_browser_profile(self, capabilities, browser_type=None):
        """ Returns updated browser profile ready to be passed to driver """
        browser_profile = None
        test_mobile = self.gid('test_mobile')
        appium_platform = self.gid('appium_platform')
        if test_mobile != 'yes' and appium_platform not in ('android', 'ios'):
            if browser_type is None:
                browser_type = capabilities['browser'].lower()
            browser_profile = self.get_browser_profile(browser_type)

            # add extensions to remote driver
            if self.gid('with_extension'):
                browser_profile = self.add_extension_to_browser(browser_type, browser_profile)

            # add Chrome options to desired capabilities
            if browser_type == 'chrome':
                chrome_capabilities = browser_profile.to_capabilities()
                capabilities.update(chrome_capabilities)
                browser_profile = None
        return browser_profile

    def add_extension_to_browser(self, browser_type, browser_profile):
        """ returns browser profile updated with one or more extensions """
        if browser_type == 'chrome':
            all_extensions = self.get_extension_file_names('crx')
            for chr_extension in all_extensions:
                browser_profile.add_extension(os.path.join(self.project_root, 'extension', chr_extension + '.crx'))
        elif browser_type == 'firefox':
            all_extensions = self.get_extension_file_names('xpi')
            for ff_extension in all_extensions:
                browser_profile.add_extension(os.path.join(self.project_root, 'extension', ff_extension + '.xpi'))
                # TODO set extension version for Firefox
                # browser_profile.set_preference("extensions." + self.gid('extension_name') + ".currentVersion",
                # self.gid('extension_version'))
        return browser_profile

    def call_browserstack_browser(self, build_name):
        """ Starts browser on BrowserStack """
        bs_auth = self.get_auth("browserstack")
        if bs_auth:
            # wait until free browserstack session is available
            self.bs_api.wait_for_free_sessions(bs_auth,
                                               int(self.gid('session_waiting_time')),
                                               int(self.gid('session_waiting_delay')))

            # get browser capabilities and profile
            capabilities = self.get_capabilities(build_name, browserstack=True)
            hub_url = 'http://{0}:{1}@hub.browserstack.com:80/wd/hub'.format(*bs_auth)

            # call remote driver
            self.start_remote_driver(hub_url, capabilities)

            session = self.bs_api.get_session(bs_auth, capabilities['build'], 'running')
            self.session_link = self.bs_api.get_session_link(session)
            self.session_id = self.bs_api.get_session_hashed_id(session)
        else:
            sys.exit('Browserstack credentials were not specified! Unable to start browser.')

    def call_browser(self, browser_type):
        """ Starts local browser """
        # get browser capabilities and profile
        appium_platform = self.gid('appium_platform')
        if appium_platform:
            capabilities = self.get_capabilities(appium_platform=appium_platform)
        else:
            capabilities = self.get_capabilities()
        remote_hub = self.gid('remote_hub')

        if remote_hub:
            self.start_remote_driver(remote_hub, capabilities, browser_type)
        else:
            self.start_local_driver(capabilities, browser_type)

    def start_remote_driver(self, remote_driver_url, capabilities, browser_type=None):
        """ Call remote browser (driver) """
        browser_profile = self.update_browser_profile(capabilities, browser_type)

        # browser type is specified (test not run on BrowserStack)
        if browser_type:
            attr = 'INTERNETEXPLORER' if browser_type == 'ie' else browser_type.upper()
            capabilities.update(getattr(DesiredCapabilities, attr, {}))
            browser_version = self.gid('browser_version')
            platform = self.gid('platform')
            if browser_version:
                capabilities['version'] = browser_version
            if platform:
                capabilities['platform'] = platform

        self.driver = webdriver.Remote(
            command_executor=remote_driver_url,
            desired_capabilities=capabilities,
            browser_profile=browser_profile)

    def start_local_driver(self, capabilities, browser_type=None):
        # add extensions to browser
        browser_profile = self.update_browser_profile(capabilities, browser_type)

        # starts local browser
        if browser_type == "firefox":
            self.driver = webdriver.Firefox(browser_profile, capabilities=capabilities)
        elif browser_type == "chrome":
            self.driver = webdriver.Chrome(desired_capabilities=capabilities, chrome_options=browser_profile)
        elif browser_type == "ie":
            self.driver = webdriver.Ie(capabilities=capabilities)
        elif browser_type == "phantomjs":
            self.driver = webdriver.PhantomJS(desired_capabilities=capabilities)
        elif browser_type == "opera":
            self.driver = webdriver.Opera(desired_capabilities=capabilities)
            # SafariDriver bindings for Python not yet implemented
            # elif browser == "Safari":
            # self.driver = webdriver.SafariDriver()

    def start_browser(self, build_name=None, url=None, browser=None, width=None, height=None):
        """ Browser startup function.
         Initialize session over Browserstack or local browser. """
        # get default parameter values
        browser, height, url, width = self.get_default_browser_attributes(browser, height, url, width)

        if browser.lower() == "browserstack":
            self.call_browserstack_browser(build_name)
        else:
            self.call_browser(browser.lower())
            self.driver.set_window_size(width, height)
        self.test_init(url)
        return self.driver

    def stop_browser(self, delete_cookies=True):
        """ Browser termination function """
        if delete_cookies:
            self.driver.delete_all_cookies()
        self.driver.quit()

    def test_init(self, url):
        """ Executed only once after browser starts.
         Suitable for general pre-test logic that do not need to run before every individual test-case. """
        self.driver.get(url)
        self.driver.implicitly_wait(int(self.gid('default_implicit_wait')))

    def start_test(self, reload_page=None):
        """ To be executed before every test-case (test function) """
        if self.session_link:
            print "Link to Browserstack report: %s " % self.session_link
        if reload_page:
            self.driver.get(self.gid('base_url'))
            self.driver.implicitly_wait(self.gid('default_implicit_wait'))
            time.sleep(5)

    def stop_test(self, test_info, execution_id=None):
        """ To be executed after every test-case (test function) """
        if test_info.test_status not in ('passed', None):
            # save screenshot in case test fails
            screenshot_folder = os.path.join(self.project_root, 'screenshots')
            if not os.path.exists(screenshot_folder):
                os.makedirs(screenshot_folder)
            file_name = re.sub('[^A-Za-z0-9_. ]+', '', test_info.test_name)
            self.driver.save_screenshot(os.path.join(screenshot_folder, file_name + '.png'))
        if execution_id:
            print "change status in Jira execution"
            auth = self.get_auth("jira")
            if test_info.test_status == "failed_execution":
                self.zapi.update_execution_status(execution_id, "FAIL", auth)
            elif test_info.test_status == "passed":
                self.zapi.update_execution_status(execution_id, "PASS", auth)

    def get_extension_file_names(self, extension_type):
        """ Method reads extension folder and gets extension file name based on provided extension type"""
        extension_location = os.path.join(self.project_root, 'extension')
        extension_file_names = []
        extension_code = self.gid('path_to_extension_code')

        # build Chrome extension from sources if required
        if extension_type == 'crx' and extension_code:
            extension_path = os.path.abspath(os.path.join(self.project_root, self.gid('path_to_extension_code')))
            if not os.path.exists(extension_location):
                os.makedirs(extension_location)
            self.build_extension()
            shutil.copy(extension_path + '.' + extension_type, extension_location)

        # find all extensions in folder (build from sources in previous step + already existing)
        if os.path.exists(extension_location):
            extension_files = glob.glob(os.path.join(extension_location, '*.' + extension_type))
            for extension in extension_files:
                extension_file_name = self.path_leaf(extension).replace('.' + extension_type, '', 1)
                extension_file_names.append(extension_file_name)
        return extension_file_names

    def path_leaf(self, path):
        """ Method reads provided path and extract last part of path. Method will return empty string if path ends
        with / (backslash)"""
        head, tail = ntpath.split(path)
        return tail or ntpath.basename(head)

    def build_extension(self):
        """ Method build Chrome extension from code provided in path in local config file."""
        # build Chrome extension
        extension_path = os.path.abspath(os.path.join(self.project_root, self.gid('path_to_extension_code')))
        shell_path = os.path.abspath(os.path.join(extension_path, os.pardir))
        extension_name = self.path_leaf(extension_path)
        os.chdir(shell_path)
        shell_command = 'crxmake ' + extension_name
        try:
            subprocess.check_call(shell_command, shell=True)
        except subprocess.CalledProcessError:
            print 'There was an issue with building extension!'

    def get_auth(self, parameter):
        auth = None
        if parameter.lower() == 'jira':
            auth = self.gid('jira_support')
        elif parameter.lower() == 'browserstack':
            auth = self.gid('browserstack')
        if auth:
            return tuple(auth.split(":"))
        return None

    def create_cycle(self, cycle_name, auth):
        cycle_id = self.zapi.create_new_test_cycle("%s %S" % (cycle_name, datetime.today().strftime("%d-%m-%y")),
                                                   self.gid('jira_project'), self.gid('jira_project_version'), auth)
        return cycle_id

    def get_execution_id(self, jira_id):
        jira_auth = self.get_auth("jira")
        if jira_auth:
            cycle_base = self.gid('jira_base_cycle')
            cycle_id = self.gid('jira_cycle_id')
            issue_id = self.zapi.get_issueid(cycle_base, jira_id, jira_auth)
            execution_id = self.zapi.add_new_execution(self.gid('jira_project'), self.gid('jira_project_version'),
                                                       cycle_id, issue_id, jira_auth)
            return execution_id