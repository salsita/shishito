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


class ControlTest():
    def __init__(self):
        self.bs_api = BrowserStackAPI()
        self.zapi = ZAPI()
        self.project_root = self.get_project_root()
        self.configs = self.load_configs()
        self.session_link = None
        self.session_id = None
        self.driver = None

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
        if not os.path.exists(config_path):
            return None
        config = ConfigParser.ConfigParser()
        # load server config variables
        server_config = os.path.join(config_path, 'server_config.properties')
        config.read(server_config)
        server_config_vars = dict(config.defaults())
        # load local config variables
        local_config = os.path.join(config_path, 'local_config.properties')
        config.read(local_config)
        local_config_vars = dict(config.defaults())
        return_configs = [server_config_vars, local_config_vars]
        return return_configs

    def gid(self, searched_id):
        """ Gets value from config variables based on provided key.
         If local execution parameter is "True", function will try to search for parameter in local configuration file.
         If such parameter is not found or there is an error while reading the file, server (default) configuration
         file will be used instead. """
        if self.configs is None:
            return None
        server_config = self.configs[0]
        local_config = self.configs[1]
        local_execution = local_config.get('local_execution')
        use_server = False
        use_environment_property = False
        value_to_return = None

        # try to retrieve value from local config
        if local_execution.lower() == 'true':
            try:
                string_returned = local_config.get(searched_id)
                if string_returned == '':
                    use_server = True
                else:
                    value_to_return = string_returned
            except:
                print('There was an error while retrieving value "' + searched_id + '" from local config!.'
                      + '\nUsing server value instead.')
                use_server = True
        else:
            use_server = True

        # try to retrieve value from server config
        if use_server:
            try:
                string_returned = server_config.get(searched_id)
                if string_returned == '':
                    use_environment_property = True
                else:
                    value_to_return = string_returned
            except:
                print('There was an error while retrieving value "' + searched_id + '" from server config!.'
                      + '\nLooking for environment property value instead.')
                use_environment_property = True

        # try to retrieve value from environment property
        if use_environment_property:
            env_property_value = os.environ.get(searched_id)
            if env_property_value is not None:
                value_to_return = env_property_value

        # raise an exception in case value could not be retrieved by any means
        if value_to_return is None:
            print('Property "' + searched_id + '" has not been found within local, server configs, neither'
                                               ' it was defined in environment property. Returning empty string')
            return ''
        return value_to_return

    def get_browserstack_capabilities(self, build_name=None):
        """ Returns dictionary of capabilities for specific Browserstack browser/os combination """
        if build_name is not None:
            build_name = build_name
        else:
            build_name = self.gid('build_name')
        test_mobile = pytest.config.getoption('test_mobile')
        if test_mobile == "yes":
            desired_cap = {'device': pytest.config.getoption('xdevice'),
                           'platform': pytest.config.getoption('xplatform'),
                           'deviceOrientation': pytest.config.getoption('xdeviceOrientation'),
                           'browserName': pytest.config.getoption('xbrowserName'),
                           'browserstack.debug': self.gid('browserstack_debug').lower(),
                           'project': self.gid('project_name'),
                           'build': build_name,
                           'name': self.get_test_name() + time.strftime('_%Y-%m-%d')}
        else:
            desired_cap = {'os': pytest.config.getoption('xos'),
                           'os_version': pytest.config.getoption('xosversion'),
                           'browser': pytest.config.getoption('xbrowser'),
                           'browser_version': pytest.config.getoption('xbrowserversion'),
                           'resolution': pytest.config.getoption('xresolution'),
                           'browserstack.debug': self.gid('browserstack_debug').lower(),
                           'project': self.gid('project_name'),
                           'build': build_name,
                           'name': self.get_test_name() + time.strftime('_%Y-%m-%d')}
        return desired_cap

    def get_capabilities(self, build_name=None, browserstack=False):
        """ Returns dictionary of browser capabilities """
        desired_cap = {}
        if bool(self.gid('accept_ssl_cert').lower() == 'false'):
            desired_cap['acceptSslCerts'] = False
        else:
            desired_cap['acceptSslCerts'] = True
        if browserstack:
            desired_cap.update(self.get_browserstack_capabilities(build_name))
        return desired_cap

    def get_test_name(self):
        """ Returns test name from the call stack, assuming there can be only
         one 'test_' file in the stack. If there are more it means two PyTest
        tests ran when calling get_test_name, which is invalid use case. """
        test_name = None
        frames = inspect.getouterframes(inspect.currentframe())
        for frame in frames:
            if re.match('test_.*', ntpath.basename(frame[1])):
                test_name = ntpath.basename(frame[1])[:-3]
                break
        if test_name is None:
            test_name = self.gid('project_name')
        return test_name

    def get_default_browser_attributes(self, browser, height, url, width):
        """ Returns default browser values if not initially set """
        if url is None:
            url = self.gid('base_url')
        if browser is None:
            browser = self.gid('driver')
        if width is None:
            width = self.gid('window_width')
        if height is None:
            height = self.gid('window_height')
        return browser, height, url, width

    def get_browser_profile(self, browser_type):
        """ returns ChromeOptions or FirefoxProfile with default settings, based on browser """
        profile = None
        if browser_type.lower() == 'chrome':
            profile = webdriver.ChromeOptions()
            profile.add_experimental_option("excludeSwitches", ["ignore-certificate-errors"])
            # set mobile device emulation
            mobile_browser_emulation = self.gid('mobile_browser_emulation')
            if bool(mobile_browser_emulation):
                profile.add_experimental_option("mobileEmulation", {"deviceName": mobile_browser_emulation})
        elif browser_type.lower() == 'firefox':
            profile = webdriver.FirefoxProfile()
        return profile

    def update_browser_profile(self, capabilities, browser_type=None):
        """ Returns updated browser profile ready to be passed to driver """
        browser_profile = None
        test_mobile = pytest.config.getoption('test_mobile')
        if not test_mobile:
            if browser_type is None:
                browser_type = capabilities['browser'].lower()
            browser_profile = self.get_browser_profile(browser_type)

            # add extensions to remote driver
            if bool(self.gid('with_extension')):
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
        # wait until free browserstack session is available
        self.bs_api.wait_for_free_sessions(bs_auth,
                                           int(self.gid('session_waiting_time')),
                                           int(self.gid('session_waiting_delay')))

        # get browser capabilities and profile
        capabilities = self.get_capabilities(build_name, browserstack=True)
        hub_url = 'http://' + bs_auth[0] + ':' + bs_auth[1] + '@hub.browserstack.com:80/wd/hub'

        # call remote driver
        self.start_remote_driver(hub_url, capabilities)

        session = self.bs_api.get_session(bs_auth, capabilities['build'], 'running')
        self.session_link = self.bs_api.get_session_link(session)
        self.session_id = self.bs_api.get_session_hashed_id(session)

    def call_browser(self, browser_type):
        """ Starts local browser """
        # get browser capabilities and profile
        capabilities = self.get_capabilities()
        remote_hub = self.gid('remote_hub')

        if bool(remote_hub):
            self.start_remote_driver(remote_hub, capabilities, browser_type)
        else:
            self.start_local_driver(capabilities, browser_type)

    def start_remote_driver(self, remote_driver_url, capabilities, browser_type=None):
        """ Call remote browser (driver) """
        browser_profile = self.update_browser_profile(capabilities, browser_type)

        # browser type is specified (test not run on BrowserStack)
        if browser_type is not None:
            driver_capabilities = {}
            if browser_type == "firefox":
                driver_capabilities = DesiredCapabilities.FIREFOX
            elif browser_type == "chrome":
                driver_capabilities = DesiredCapabilities.CHROME
            elif browser_type == "ie":
                driver_capabilities = DesiredCapabilities.INTERNETEXPLORER
            elif browser_type == "phantomjs":
                driver_capabilities = DesiredCapabilities.PHANTOMJS
            elif browser_type == "opera":
                driver_capabilities = DesiredCapabilities.OPERA
            capabilities.update(driver_capabilities)
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
        if self.session_link is not None:
            print ("Link to Browserstack report: %s " % self.session_link)
        if reload_page is not None:
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
        if execution_id is not None:
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
            print('There was an issue with building extension!')

    def get_auth(self, parameter):
        auth = None
        if parameter.lower() == 'jira':
            auth = pytest.config.getoption('jira_support')
        elif parameter.lower() == 'browserstack':
            auth = pytest.config.getoption('browserstack')
        if auth:
            credentials = auth.split(":")
            return str(credentials[0]), str(credentials[1])
        return None

    def create_cycle(self, cycle_name, auth):
        cycle_id = self.zapi.create_new_test_cycle(cycle_name + " " + datetime.today().strftime("%d-%m-%y"),
                                                   self.gid('jira_project'), self.gid('jira_project_version'), auth)
        return cycle_id

    def get_execution_id(self, jira_id):
        jira_auth = self.get_auth("jira")
        if jira_auth:
            cycle_base = self.gid('jira_base_cycle')
            cycle_id = pytest.config.getoption('jira_cycle_id')
            issue_id = self.zapi.get_issueid(cycle_base, jira_id, jira_auth)
            execution_id = self.zapi.add_new_execution(self.gid('jira_project'), self.gid('jira_project_version'),
                                                       cycle_id, issue_id, jira_auth)
            return execution_id
        return None