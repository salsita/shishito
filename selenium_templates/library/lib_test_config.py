# /usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: Vojtech Burian
@summary: Common function library
"""
import ConfigParser
from selenium import webdriver
import os
import sys
import inspect
import pytest
import time


def config_loader():
    """ loads variables from .properties configuration files """
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


def get_capabilities():
    """ Returns dictionary of capabilities for specific Browserstack browser/os combination """
    testname = os.path.basename(inspect.getsourcefile(sys._getframe(2)))[:-3]
    desired_cap = {'os': pytest.config.getoption('xos'),
                   'os_version': pytest.config.getoption('xosversion'),
                   'browser': pytest.config.getoption('xbrowser'),
                   'browser_version': pytest.config.getoption('xbrowserversion'),
                   'resolution': pytest.config.getoption('xresolution'),
                   'project': gid('project_name'),
                   'build': pytest.config.getoption('xbuildname'),
                   'name': testname + time.strftime('_%Y-%m-%d')}
    return desired_cap


def start_browser(self, url=gid('base_url'),
                  browser=gid('driver'), width=gid('window_width'),
                  height=gid('window_height')):
    """ Browser startup function.
     Initialize session over Browserstack or local browser. """
    if browser.lower() == "browserstack":
        bs_username = gid('bs_username')
        bs_password = gid('bs_password')
        command_executor = 'http://' + bs_username + ':' + bs_password + '@hub.browserstack.com:80/wd/hub'
        self.driver = webdriver.Remote(
            command_executor=command_executor,
            desired_capabilities=get_capabilities())
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