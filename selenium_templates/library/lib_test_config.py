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
from library.browserstack_api import BrowserStackAPI
from tests.conftest import get_test_info

bs_api = BrowserStackAPI()


def config_loader():
    """ Loads variables from .properties configuration files """
    dir_path = os.path.dirname(os.path.abspath(__file__))
    config = ConfigParser.ConfigParser()

    # load server config variables
    config.read(dir_path + '/../config/server_config.properties')
    server_config_vars = dict(config.defaults())

    # load local config variables
    config.read(dir_path + '/../config/local_config.properties')
    local_config_vars = dict(config.defaults())

    return_configs = [server_config_vars, local_config_vars]
    return return_configs


def gid(searched_id):
    """ Gets value from config variables based on provided key.
     If local execution parameter is "True", function will try to search for parameter in local configuration file.
     If such parameter is not found or there is an error while reading the file, server (default) configuration
     file will be used instead. """
    config_vars = config_loader()
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


def get_capabilities(build_name=None):
    """ Returns dictionary of capabilities for specific Browserstack browser/os combination """
    if build_name is not None:
         build_name= build_name
    else:
         build_name= gid('build_name')
    test_name = os.path.basename(inspect.getsourcefile(sys._getframe(2)))[:-3]
    desired_cap = {'os': pytest.config.getoption('xos'),
                   'os_version': pytest.config.getoption('xosversion'),
                   'browser': pytest.config.getoption('xbrowser'),
                   'browser_version': pytest.config.getoption('xbrowserversion'),
                   'resolution': pytest.config.getoption('xresolution'),
                   'project': gid('project_name'),
                   'build': build_name,
                   'name': test_name + time.strftime('_%Y-%m-%d')}
    return desired_cap


def start_browser(self, build_name=None, url=gid('base_url'),
                  browser=gid('driver'), width=gid('window_width'),
                  height=gid('window_height')):
    """ Browser startup function.
     Initialize session over Browserstack or local browser. """
    self.session_link=None
    if browser.lower() == "browserstack":
        bs_username = gid('bs_username')
        bs_password = gid('bs_password')
        bs_api.wait_for_free_sessions((bs_username, bs_password), 2, 1)
        capabilities = get_capabilities(build_name)
        command_executor = 'http://' + bs_username + ':' + bs_password + '@hub.browserstack.com:80/wd/hub'
        self.driver = webdriver.Remote(
            command_executor=command_executor,
            desired_capabilities=capabilities)
        auth=(bs_username,bs_password)
        session=bs_api.get_session(auth, capabilities['build'], 'running')
        self.session_link=bs_api.get_session_link(session)
        self.session_id=bs_api.get_session_hashed_id(session)

    elif browser == "Firefox":
        self.driver = webdriver.Firefox()
    elif browser == "Chrome":
        self.driver = webdriver.Chrome()
    elif browser == "IE":
        self.driver = webdriver.Ie()
    elif browser == "PhantomJS":
        self.driver = webdriver.PhantomJS()
    elif browser == "Opera":
        self.driver = webdriver.OperaDriver()
    elif browser == "Safari":
        self.driver = webdriver.SafariDriver()

    if browser.lower() != "browserstack":
        self.driver.set_window_size(width, height)
    self.driver.get(url)
    self.driver.implicitly_wait(int(gid('default_implicit_wait')))
    return self.driver


def stop_browser(self, delete_cookies=True):
    """ Browser termination function """
    if delete_cookies:
        self.driver.delete_all_cookies()
    self.driver.quit()


def start_test(self, reload=None):
    """ Executed before every test-case (test function) """
    if self.session_link is not None:
        print ("Link to Browserstack report: %s "% self.session_link)
    if reload is not None:
        self.driver.get(gid('base_url'))
        self.driver.implicitly_wait(gid('default_implicit_wait'))
        time.sleep(5)


def stop_test(self):
    test_info = get_test_info()
    if test_info.test_status not in ('passed', None):
        # save screenshot in case test fails
        screenshot_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'screenshots')
        if not os.path.exists(screenshot_folder):
            os.makedirs(screenshot_folder)
        file_name = re.sub('[^A-Za-z0-9_. ]+', '', test_info.test_name)
        self.driver.save_screenshot(os.path.join(screenshot_folder, file_name + '.png'))