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

from selenium import webdriver
import pytest

from salsa_webqa.library.support.browserstack import BrowserStackAPI


bs_api = BrowserStackAPI()


class TestControl():
    def __init__(self):
        self.bs_api = BrowserStackAPI()
        self.project_root = self.get_project_root()
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
        """ Loads variables from .properties configuration files """
        config_path = os.path.join(self.project_root, 'config')
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
        config_vars = self.load_configs()
        server_config = config_vars[0]
        local_config = config_vars[1]
        local_execution = local_config.get('local_execution')
        use_server = True

        if local_execution.lower() == 'true':
            try:
                searched_value = local_config.get(searched_id)
                if searched_value != '':
                    use_server = False
            except:
                print('There was an error while retrieving value "' + searched_id + '" from local config!.'
                      + '\nUsing server value instead.')
        if use_server:
            value_to_return = server_config.get(searched_id)
        else:
            value_to_return = local_config.get(searched_id)

        return value_to_return

    def get_capabilities(self, build_name=None):
        """ Returns dictionary of capabilities for specific Browserstack browser/os combination """
        if build_name is not None:
            build_name = build_name
        else:
            build_name = self.gid('build_name')
        # TODO need to change the way how to set test name
        # this is no longer reliable now that user can override any kind of method in his/her custom library
        # because of this there the call stack can have various depth
        test_name = os.path.basename(inspect.getsourcefile(sys._getframe(2)))[:-3]
        desired_cap = {'os': pytest.config.getoption('xos'),
                       'os_version': pytest.config.getoption('xosversion'),
                       'browser': pytest.config.getoption('xbrowser'),
                       'browser_version': pytest.config.getoption('xbrowserversion'),
                       'resolution': pytest.config.getoption('xresolution'),
                       'project': self.gid('project_name'),
                       'build': build_name,
                       'name': test_name + time.strftime('_%Y-%m-%d')}
        return desired_cap

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

    def call_browserstack_browser(self, build_name):
        """ Starts browser on BrowserStack """
        bs_username = self.gid('bs_username')
        bs_password = self.gid('bs_password')
        self.bs_api.wait_for_free_sessions((bs_username, bs_password), 2, 1)
        capabilities = self.get_capabilities(build_name)
        command_executor = 'http://' + bs_username + ':' + bs_password + '@hub.browserstack.com:80/wd/hub'
        self.driver = webdriver.Remote(
            command_executor=command_executor,
            desired_capabilities=capabilities)
        auth = (bs_username, bs_password)
        session = self.bs_api.get_session(auth, capabilities['build'], 'running')
        self.session_link = self.bs_api.get_session_link(session)
        self.session_id = self.bs_api.get_session_hashed_id(session)

    def call_local_browser(self, browser):
        """ Starts local browser """
        if browser == "Firefox":
            self.driver = webdriver.Firefox()
        elif browser == "Chrome":
            self.driver = webdriver.Chrome()
        elif browser == "IE":
            self.driver = webdriver.Ie()
        elif browser == "PhantomJS":
            self.driver = webdriver.PhantomJS()
        elif browser == "Opera":
            self.driver = webdriver.Opera()
        # SafariDriver bindings for Python not yet implemented
        # elif browser == "Safari":
        #     self.driver = webdriver.SafariDriver()

    def start_browser(self, build_name=None, url=None, browser=None, width=None, height=None):
        """ Browser startup function.
         Initialize session over Browserstack or local browser. """
        # get default parameter values
        browser, height, url, width = self.get_default_browser_attributes(browser, height, url, width)

        if browser.lower() == "browserstack":
            self.call_browserstack_browser(build_name)
        else:
            self.call_local_browser(browser)
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

    def start_test(self, reload=None):
        """ To be executed before every test-case (test function) """
        if self.session_link is not None:
            print ("Link to Browserstack report: %s " % self.session_link)
        if reload is not None:
            self.driver.get(self.gid('base_url'))
            self.driver.implicitly_wait(self.gid('default_implicit_wait'))
            time.sleep(5)

    def stop_test(self, test_info):
        """ To be executed after every test-case (test function) """
        if test_info.test_status not in ('passed', None):
            # save screenshot in case test fails
            screenshot_folder = os.path.join(self.project_root, 'screenshots')
            if not os.path.exists(screenshot_folder):
                os.makedirs(screenshot_folder)
            file_name = re.sub('[^A-Za-z0-9_. ]+', '', test_info.test_name)
            self.driver.save_screenshot(os.path.join(screenshot_folder, file_name + '.png'))